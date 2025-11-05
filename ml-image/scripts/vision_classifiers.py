import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import transforms, models
from torch.cuda.amp import autocast

from .utils import ImageDataset

# https://github.com/alihassanml/Yolo11-Face-Emotion-Detection
# Face emotion detection ?


class VisionClassifier:
    def __init__(self, device: str = None, num_cpu_threads: int = 1) -> None:
        # add more models here as we see fit, can also swap current models for smaller models

        if not device:
            self.device = torch.device(
                'cuda') if torch.cuda.is_available() else torch.device('cpu')
        else:
            self.device = torch.device(device)

        torch.set_num_threads(num_cpu_threads)

        self.model_fair_7 = models.resnet34(weights=models.ResNet34_Weights.IMAGENET1K_V1)
        # self.model_fair_7 = models.resnet34(pretrained=True)
        self.model_fair_7.fc = torch.nn.Linear(
            self.model_fair_7.fc.in_features, 18)
        fair_7_state_dict = torch.load(
            'models/res34_fair_align_multi_7_20190809.pt', map_location=self.device)
        self.model_fair_7.load_state_dict(fair_7_state_dict)
        self.model_fair_7.to(self.device).eval()
        # https://github.com/dchen236/FairFace/tree/master
        # weights available @ https://drive.google.com/file/d/113QMzQzkBDmYMs9LwzvD-jxEZdBQ5J4X/view?usp=drive_link

    def predict_age_gender_ethnicity(
            self, faces: list, batch_size: int = 64, expose_confs: bool = False
    ) -> tuple[list, list, list, list, list, list]:

        ethnicity_labels = {
            0: 'White', 1: 'Black', 2: 'Latino_Hispanic', 3: 'East Asian',
            4: 'Southeast Asian', 5: 'Indian', 6: 'Middle Eastern',
        }

        gender_labels = {
            0: 'Male', 1: 'Female',
        }

        age_labels = {
            0: '0-2', 1: '3-9', 2: '10-19', 3: '20-29', 4: '30-39',
            5: '40-49', 6: '50-59', 7: '60-69', 8: '70+',
        }

        inference_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[
                                 0.229, 0.224, 0.225]),
        ])

        transformed_faces = ImageDataset(faces, inference_transform)
        # Use pin_memory for faster GPU transfer
        pin_mem = self.device.type == 'cuda'
        dataloader = DataLoader(
            transformed_faces, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_mem)

        ages, genders, ethnicities = [], [], []
        age_confidences, gender_confidences, ethnicity_confidences = [], [], []
        use_amp = self.device.type == 'cuda'  # Use mixed precision on CUDA
        
        with torch.no_grad():
            for batch in dataloader:
                batch = batch.to(self.device, non_blocking=True)
                
                # Use automatic mixed precision for memory efficiency
                with autocast(enabled=use_amp):
                    outputs = self.model_fair_7(batch)
                
                outputs_cpu = outputs.detach().cpu()

                age_outputs = outputs_cpu[:, 9:18]
                gender_outputs = outputs_cpu[:, 7:9]
                ethnicity_outputs = outputs_cpu[:, :7]

                # get confidence scores and argmax of predictions
                age_results = torch.max(
                    torch.softmax(age_outputs, dim=1), dim=1)
                gender_results = torch.max(
                    torch.softmax(gender_outputs, dim=1), dim=1)
                ethnicity_results = torch.max(
                    torch.softmax(ethnicity_outputs, dim=1), dim=1)

                ages.extend(age_results.indices.tolist())
                genders.extend(gender_results.indices.tolist())
                ethnicities.extend(ethnicity_results.indices.tolist())

                if expose_confs:
                    age_confs = torch.softmax(age_outputs, dim=1).tolist()
                    gender_confs = torch.softmax(
                        gender_outputs, dim=1).tolist()
                    ethnicity_confs = torch.softmax(
                        ethnicity_outputs, dim=1).tolist()
                    age_confidences.extend(age_confs)
                    gender_confidences.extend(gender_confs)
                    ethnicity_confidences.extend(ethnicity_confs)
                else:
                    age_confidences.extend(age_results.values.tolist())
                    gender_confidences.extend(gender_results.values.tolist())
                    ethnicity_confidences.extend(
                        ethnicity_results.values.tolist())
                
                # Clear intermediate variables
                del batch, outputs, outputs_cpu
        
        # Clear cache after classification
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        ages = [age_labels[age] for age in ages]
        genders = [gender_labels[gender] for gender in genders]
        ethnicities = [ethnicity_labels[ethnicity]
                       for ethnicity in ethnicities]

        return ages, genders, ethnicities, age_confidences, gender_confidences, ethnicity_confidences


class FaceAttributeClassifier:
    """
    Classifier for face attributes using CelebA-HQ model.
    Predicts 40 different facial attributes like glasses, beard, makeup, etc.
    """
    
    ATTRIBUTES = [
        '5_o_Clock_Shadow', 'Arched_Eyebrows', 'Attractive', 'Bags_Under_Eyes', 
        'Bald', 'Bangs', 'Big_Lips', 'Big_Nose', 'Black_Hair', 'Blond_Hair', 
        'Brown_Hair', 'Bushy_Eyebrows', 'Chubby', 'Double_Chin', 'Eyeglasses', 
        'Goatee', 'Gray_Hair', 'Heavy_Makeup', 'High_Cheekbones', 'Male', 
        'Mouth_Slightly_Open', 'Mustache', 'Narrow_Eyes', 'No_Beard', 'Oval_Face', 
        'Pale_Skin', 'Pointy_Nose', 'Receding_Hairline', 'Rosy_Cheeks', 
        'Sideburns', 'Smiling', 'Straight_Hair', 'Wavy_Hair', 'Wearing_Earrings', 
        'Wearing_Hat', 'Wearing_Lipstick', 'Wearing_Necklace', 'Wearing_Necktie', 
        'Young'
    ]
    
    def __init__(self, model_path: str = 'models/celeba_atributes_classification.ckpt', device: str = None, num_cpu_threads: int = 1) -> None:
        if not device:
            self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        else:
            self.device = torch.device(device)
        
        torch.set_num_threads(num_cpu_threads)
        
        # Load checkpoint to detect model architecture
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Extract state_dict from PyTorch Lightning checkpoint if needed
        if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        elif isinstance(checkpoint, dict):
            state_dict = checkpoint
        else:
            state_dict = checkpoint
        
        # Detect if it's a ViT or ResNet model based on keys
        is_vit = any('patch_embed' in k or 'blocks' in k or 'cls_token' in k for k in state_dict.keys())
        
        if is_vit:
            # Import timm for Vision Transformer
            try:
                import timm
            except ImportError:
                raise ImportError("timm library required for ViT models. Install with: pip install timm")
            
            # Create ViT model
            self.model = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=40)
            
            # Remove 'net.' prefix from state_dict keys for ViT checkpoints
            state_dict = {k.replace('net.', ''): v for k, v in state_dict.items()}
            
            # Load with strict=False to handle minor mismatches
            self.model.load_state_dict(state_dict, strict=False)
        else:
            # ResNet50 model
            self.model = models.resnet50(weights=None)
            self.model.fc = torch.nn.Linear(self.model.fc.in_features, 40)
            
            # Remove common prefixes
            state_dict = {k.replace('model.', ''): v for k, v in state_dict.items()}
            self.model.load_state_dict(state_dict)
        
        self.model.to(self.device).eval()
    
    def predict_attributes(
            self, faces: list, batch_size: int = 64, return_probs: bool = False
    ) -> list[dict]:
        """
        Predict facial attributes for a list of face images.
        
        Args:
            faces: List of face images (numpy arrays)
            batch_size: Batch size for inference
            return_probs: If True, return probability scores instead of binary predictions
            
        Returns:
            List of dictionaries, each containing attribute predictions for one face
        """
        inference_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        transformed_faces = ImageDataset(faces, inference_transform)
        pin_mem = self.device.type == 'cuda'
        dataloader = DataLoader(
            transformed_faces, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_mem
        )
        
        all_attributes = []
        use_amp = self.device.type == 'cuda'
        
        with torch.no_grad():
            for batch in dataloader:
                batch = batch.to(self.device, non_blocking=True)
                
                with autocast(enabled=use_amp):
                    outputs = self.model(batch)
                
                # Apply sigmoid to get probabilities
                probs = torch.sigmoid(outputs).detach().cpu().numpy()
                
                # Convert to binary predictions or keep probabilities
                for face_probs in probs:
                    if return_probs:
                        attributes_dict = {attr: float(face_probs[i]) for i, attr in enumerate(self.ATTRIBUTES)}
                    else:
                        attributes_dict = {attr: bool(face_probs[i] > 0.5) for i, attr in enumerate(self.ATTRIBUTES)}
                    all_attributes.append(attributes_dict)
                
                del batch, outputs
        
        # Clear cache after inference
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        return all_attributes


def classify_faces(
        filtered_detections: list[dict], batch_size: int, device: str, source_type: str="trailer", gender_conf_threshold: float = 0.965932283883782, age_conf_threshold: float = 0.5956672158338605, ethnicity_conf_threshold: float = 0.810392266540905
        ) -> tuple[list[dict], list[np.array]]:
    # Classify all filtered faces
    classifier = VisionClassifier(device=device)
    
    flattened_faces = [det["cropped_face"] for det in filtered_detections]
    if len(flattened_faces) > 0:
        ages, genders, ethnicities, age_confs, gender_confs, ethnicity_confs = classifier.predict_age_gender_ethnicity(
            flattened_faces, batch_size = batch_size)

        match source_type:
            case "trailer":
                for i, det in enumerate(filtered_detections):
                    det["gender"] = genders[i] if gender_confs[i] >= gender_conf_threshold else "unknown"
                    det["gender_conf"] = gender_confs[i]
                    det["age"] = ages[i] if age_confs[i] >= age_conf_threshold else "unknown"
                    det["age_conf"] = age_confs[i]
                    det["ethnicity"] = ethnicities[i] if ethnicity_confs[i] >= ethnicity_conf_threshold else "unknown"
                    det["ethnicity_conf"] = ethnicity_confs[i]
            
            case "poster":
                for i, det in enumerate(filtered_detections):
                    det["gender"] = genders[i]
                    det["age"] = ages[i]
                    det["ethnicity"] = ethnicities[i]

            case _:
                raise ValueError(f"Invalid source_type: {source_type}. Choose either 'trailer' or 'poster'.")
    
    return filtered_detections, flattened_faces


def extract_face_attributes(
        filtered_detections: list[dict],
        batch_size: int,
        device: str,
        model_path: str = 'models/celeba_atributes_classification.ckpt',
        return_probs: bool = False
) -> list[dict]:
    """
    Extract facial attributes (glasses, beard, makeup, etc.) for detected faces.
    
    Args:
        filtered_detections: List of detection dictionaries with 'cropped_face' key
        batch_size: Batch size for inference
        device: Device to run inference on ('cuda' or 'cpu')
        model_path: Path to the CelebA-HQ model weights
        return_probs: If True, return probability scores instead of binary predictions
        
    Returns:
        filtered_detections with added 'attributes' key containing predicted attributes
    """
    attribute_classifier = FaceAttributeClassifier(model_path=model_path, device=device)
    
    flattened_faces = [det["cropped_face"] for det in filtered_detections]
    
    if len(flattened_faces) > 0:
        attributes_list = attribute_classifier.predict_attributes(
            flattened_faces, batch_size=batch_size, return_probs=return_probs
        )
        
        for i, det in enumerate(filtered_detections):
            det["attributes"] = attributes_list[i]
    
    return filtered_detections
