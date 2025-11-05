import cv2
import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import transforms
from ultralytics import YOLO
from torch.cuda.amp import autocast

from .utils import ImageDataset


class VisionDetection:
    def __init__(self, device: str = None, num_cpu_threads: int = 1, H_resize: int = 640, W_resize: int = 640) -> None:
        # add more models here as we see fit, can also swap current models for smaller models

        if not device:
            self.device = torch.device(
                'cuda') if torch.cuda.is_available() else torch.device('cpu')
        else:
            self.device = torch.device(device)

        torch.set_num_threads(num_cpu_threads)

        self.H_resized, self.W_resized = H_resize, W_resize

        self.yolo_model_person = YOLO(
            'models/yolo11l.pt').to(self.device).eval()
        # https://github.com/ultralytics/ultralytics

        self.yolo_model_face = YOLO(
            'models/yolov11n-face.pt').to(self.device).eval()

        # https://github.com/akanametov/yolo-face

        #print("VisionDetection initialized with device:", self.device)

    def get_areas_of_interest(
            self, images: np.ndarray, area_type: str = "face", batch_size: int = 64) -> list:
        """
        Extract areas of interest (faces, silhouettes) from a list of images.
        """
        # Transformation for YOLO model
        if len(images.shape) == 3:  # Single image: [H, W, C]
            images = np.expand_dims(images, axis=0)  # Convert to batch: [1, H, W, C]

        if len(images.shape) != 4:  # Ensure batch format: [N, H, W, C]
            raise ValueError("Input images must have shape [H, W, C] or [N, H, W, C]")

        def bgr_to_rgb(image):
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Define transformations
        frames_transform = transforms.Compose([
            transforms.Lambda(lambda img: bgr_to_rgb(img)),
            transforms.ToTensor(),
            # Resize for YOLO model
            transforms.Resize((self.H_resized, self.W_resized)),
        ])

        # Load frames in the dataloader
        dataset = ImageDataset(images, frames_transform)
        # Use pin_memory for faster GPU transfer
        pin_mem = self.device.type == 'cuda'
        dataloader = DataLoader(
            dataset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=pin_mem)

        # Detect faces in all frames of the trailer
        results = []
        use_amp = self.device.type == 'cuda'  # Use mixed precision on CUDA
        
        with torch.no_grad():
            if area_type == "face":
                for batch in dataloader:
                    batch = batch.to(self.device, non_blocking=True)
                    batch = torch.clamp(batch, 0, 1)  # Ensure values are in [0, 1] range
                    with autocast(enabled=use_amp):
                        detections = self.yolo_model_face(batch, verbose=False)
                    results.extend(detections)
                    # Clear batch from memory
                    del batch
            else:
                for batch in dataloader:
                    batch = batch.to(self.device, non_blocking=True)
                    batch = torch.clamp(batch, 0, 1)  # Ensure values are in [0, 1] range
                    with autocast(enabled=use_amp):
                        detections = self.yolo_model_person(batch, verbose=False, classes=[0])
                    results.extend(detections)
                    # Clear batch from memory
                    del batch
        
        # Clear cache after detection
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return results

    def crop_areas_of_interest(
            self, images: np.ndarray, H_original: int, W_original: int, area_type: str = 'face', batch_size: int = 64, bbox_expand_factor: float = 0) -> list[dict]:
        """
        Create individual subimages for all areas of interest in one image
        
        Parameters:
            bbox_expand_factor: Factor to expand bounding boxes (e.g., 0.3 = 30% expansion on each side)
                               This helps include more context like hair for face crops
        """
        areas_of_interest = self.get_areas_of_interest(
            images, area_type, batch_size=batch_size)

        # Rescaling factors determination
        scale_x = W_original / self.W_resized
        scale_y = H_original / self.H_resized

        detections = []
        for k, area in enumerate(areas_of_interest):
            for i in range(len(area.boxes)):
                x1, y1, x2, y2 = map(int, area.boxes[i].xyxy[0])
                # Bounding boxes need to be rescaled as we previously changed frames size
                x1, x2, y1, y2 = int(
                     x1 * scale_x), int(x2 * scale_x), int(y1 * scale_y), int(y2 * scale_y)
                
                # Expand bounding box to include more context (e.g., hair)
                if bbox_expand_factor > 0:
                    width = x2 - x1
                    height = y2 - y1
                    expand_x = int(width * bbox_expand_factor)
                    expand_y = int(height * bbox_expand_factor)
                    
                    # Expand and clip to image boundaries
                    x1_expanded = max(0, x1 - expand_x)
                    y1_expanded = max(0, y1 - expand_y)
                    x2_expanded = min(W_original, x2 + expand_x)
                    y2_expanded = min(H_original, y2 + expand_y)
                else:
                    x1_expanded, y1_expanded = x1, y1
                    x2_expanded, y2_expanded = x2, y2
                
                conf = area.boxes[i].conf.item()
                match len(images.shape):
                    case 3:
                        cropped_image = images[y1_expanded:y2_expanded, x1_expanded:x2_expanded]
                    case 4:
                        cropped_image = images[k][y1_expanded:y2_expanded, x1_expanded:x2_expanded]
                    case _:
                        raise ValueError("Input images must have shape [H, W, C] or [N, H, W, C]")
                detections.append({"bbox": [
                     x1_expanded, y1_expanded, x2_expanded, y2_expanded], "conf": conf, "frame_id": k, "perso_id": i, f"cropped_{area_type}": cropped_image})
    
        return detections

    
def link_faces_to_bodies(detections, body_detections):
    """
    Link faces to bodies based on bounding box overlap.
    """
    linked_detections = []

    for face in detections:
        face_bbox = face["bbox"]  # Face bounding box 
        body_faces_candidates = []

        for id, body in enumerate(body_detections):
            body_bbox = body["bbox"]  # Body bounding box 

            # Check if the face is inside the body bounding box
            if (
                face_bbox[0] >= body_bbox[0] and 
                face_bbox[1] >= body_bbox[1] and 
                face_bbox[2] <= body_bbox[2] and  
                face_bbox[3] <= body_bbox[3]    
            ):
                # Compute IoU
                iou = compute_I_o_U(face_bbox, body_bbox)
                body_faces_candidates.append((body, id, iou))
        
        match len(body_faces_candidates):
            case 0:
                # No body found for this face, add the face only
                linked_detections.append({
                    "body_bbox": face["bbox"],
                    "bbox": face["bbox"],
                    "gender": face["gender"],
                    "age": face["age"],
                    "ethnicity": face["ethnicity"]
                })
            
            case _:
                # Sort candidates by IoU and take the one with the highest IoU
                body_faces_candidates.sort(key=lambda x: x[2], reverse=True)
                body, id, _= body_faces_candidates[0]  # Take the body with the highest IoU
                body_detections.pop(id)  # Remove the body from the list to avoid duplicates
                # Add the linked face and body to the list
                linked_detections.append({
                    "body_bbox": body["bbox"],
                    "bbox": face["bbox"],
                    "gender": face["gender"],
                    "age": face["age"],
                    "ethnicity": face["ethnicity"]
                })

    return linked_detections


def compute_I_o_U(face_bbox, body_bbox):
    """
    Compute the Intersection over Union (IoU) between two bounding boxes.
    
    Parameters:
        face_bbox (list): Bounding box of the face [x1, y1, x2, y2].
        body_bbox (list): Bounding box of the body [x1, y1, x2, y2].

    Returns:
        float: IoU value.
    """
    # Calculate the coordinates of the intersection rectangle
    x1_inter = max(face_bbox[0], body_bbox[0])
    y1_inter = max(face_bbox[1], body_bbox[1])
    x2_inter = min(face_bbox[2], body_bbox[2])
    y2_inter = min(face_bbox[3], body_bbox[3])

    # Calculate the area of intersection rectangle
    inter_area = max(0, x2_inter - x1_inter) * max(0, y2_inter - y1_inter)

    # Calculate the area of both bounding boxes
    face_area = (face_bbox[2] - face_bbox[0]) * (face_bbox[3] - face_bbox[1])
    body_area = (body_bbox[2] - body_bbox[0]) * (body_bbox[3] - body_bbox[1])

    # Calculate the area of union
    union_area = face_area + body_area - inter_area

    # Calculate IoU
    iou = inter_area / union_area if union_area > 0 else 0

    return iou


def detect_faces(
        frames: np.array, H_original: int, W_original: int, area_type: str, batch_size: int, device: str, num_cpu_threads: int, bbox_expand_factor: float = 0) -> list[dict]:
    """
    Detect faces in the video
    
    Parameters:
        bbox_expand_factor: Factor to expand bounding boxes (default 0 = no expansion)
                           Set higher (e.g., 0.5) to include more hair/context
    """
    # Detect faces in the video
    vision_detector = VisionDetection(
        device=device, num_cpu_threads=num_cpu_threads)
    detections = vision_detector.crop_areas_of_interest(
        frames, H_original, W_original, area_type=area_type, batch_size=batch_size, bbox_expand_factor=bbox_expand_factor)

    return detections
