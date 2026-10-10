"""Création d'un dossier immuable depuis une image et des prédictions."""
import io
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps

from .files import atomic_json, digest


def prepare(root, poster_id, image_bytes, predictions, metadata):
    import re
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', poster_id):
        raise ValueError('Identifiant invalide')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / poster_id
    if target.exists():
        raise FileExistsError('Dossier déjà présent : utiliser un nouvel identifiant')
    work = Path(tempfile.mkdtemp(prefix='.import-', dir=root))
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source).convert('RGB')
            if source.format == 'JPEG' and source.getexif().get(274, 1) == 1:
                (work / 'image.jpg').write_bytes(image_bytes)
            else:
                image.save(work / 'image.jpg', quality=95)
            width, height = image.size
        # Valider le contrat sans importer FastAPI/Pydantic dans l’environnement ML.
        from math import isfinite
        faces = []
        for prediction in predictions:
            p = dict(prediction)
            if set(p) - {'id', 'bbox', 'gender', 'age_range', 'detection_confidence', 'provenance'}:
                raise ValueError('Champs de prédiction inconnus')
            if not isinstance(p.get('id'), str) or not 0 < len(p['id']) <= 100:
                raise ValueError('Identifiant de prédiction invalide')
            if p.get('gender') not in (None, 'female', 'male', 'unknown'):
                raise ValueError('Genre invalide')
            if p.get('age_range') not in (None, '0-2', '3-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70+', 'unknown'):
                raise ValueError('Tranche d’âge invalide')
            conf = p.get('detection_confidence')
            if conf is not None and (not isfinite(conf) or not 0 <= conf <= 1):
                raise ValueError('Confiance invalide')
            p.setdefault('gender', None)
            p.setdefault('age_range', None)
            p.setdefault('detection_confidence', None)
            p.setdefault('provenance', 'trailer_match')
            faces.append(p)
        if len({p['id'] for p in faces}) != len(faces):
            raise ValueError('Identifiants de prédictions dupliqués')
        for p in faces:
            x1, y1, x2, y2 = p['bbox']
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                raise ValueError('Boîte hors image')
        manifest = dict(metadata, schema_version=1, id=poster_id, width=width, height=height,
                        image_sha256=digest(work / 'image.jpg'),
                        created_at=datetime.now(timezone.utc).isoformat())
        atomic_json(work / 'manifest.json', manifest)
        atomic_json(work / 'predictions.json', faces)
        work.rename(target)
    finally:
        if work.exists():
            shutil.rmtree(work)
    return manifest


def convert_predictions(detections):
    """Ne conserve ni embeddings, ni crops, ni ethnie des sorties ML."""
    faces = []
    for i, d in enumerate(detections):
        gender = d.get('gender')
        gender = str(gender).lower() if gender is not None else None
        age = d.get('age')
        age = str(age).lower() if age is not None else None
        faces.append(dict(id=f'p{i + 1}', bbox=[float(v) for v in d['bbox']], gender=gender,
                          age_range=age, detection_confidence=float(d['conf']) if 'conf' in d else None,
                          provenance='trailer_match'))
    return faces


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Préparer une affiche pour annotation locale')
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--allocine-id', type=int)
    parser.add_argument('--root', type=Path, default=Path('ml-image/annotation-poster/data'))
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--predictions', type=Path, help='Liste JSON conforme au contrat Prediction')
    inputs.add_argument('--trusted-pickle', type=Path, help='UNIQUEMENT un pickle local de confiance')
    parser.add_argument('--metadata', type=Path, help='JSON avec run_id, code_version, weights, parameters')
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text()) if args.metadata else {}
    predictions = []
    if args.predictions:
        predictions = json.loads(args.predictions.read_text())
    elif args.trusted_pickle:
        import pickle
        with args.trusted_pickle.open('rb') as stream:
            predictions = convert_predictions(pickle.load(stream))
    metadata.update(title=args.title, allocine_id=args.allocine_id,
                    prediction_stage='filtered' if args.predictions or args.trusted_pickle else 'none')
    for key in ('run_id', 'code_version', 'weights', 'parameters'):
        metadata.setdefault(key, None)
    prepare(args.root, args.id, args.image.read_bytes(), predictions, metadata)
    print(f'Affiche préparée : {args.root / args.id}')


if __name__ == '__main__':
    main()
