"""Stockage local atomique, verrouillé entre processus et onglets."""
import fcntl
import json
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

from .models import Annotation, Prediction, Review


from .files import atomic_json, digest


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def folder(self, poster_id):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', poster_id):
            raise HTTPException(400, 'Identifiant invalide')
        path = self.root / poster_id
        if path.is_symlink() or not path.is_dir():
            raise HTTPException(404, 'Affiche absente')
        return path

    @contextmanager
    def locked(self, path):
        with (path / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def read(self, path, name):
        target = path / name
        if target.is_symlink():
            raise HTTPException(409, 'Fichier symbolique non accepté')
        return json.loads(target.read_text())

    def load(self, poster_id):
        path = self.folder(poster_id)
        manifest = self.read(path, 'manifest.json')
        if manifest.get('schema_version') != 1:
            raise HTTPException(409, 'Version de dossier non prise en charge')
        image = path / 'image.jpg'
        if image.is_symlink() or digest(image) != manifest['image_sha256']:
            raise HTTPException(409, 'L’image a changé ; préparer un nouveau dossier')
        predictions = [Prediction.model_validate(p) for p in self.read(path, 'predictions.json')]
        if (path / 'review.json').exists():
            review = Review.model_validate(self.read(path, 'review.json'))
            if review.image_sha256 != manifest['image_sha256']:
                raise HTTPException(409, 'Relecture liée à une autre image')
        else:
            review = Review(image_sha256=manifest['image_sha256'], annotator='local', annotations=[
                Annotation(**p.model_dump(include={'id', 'bbox', 'gender', 'age_range'}),
                           source_prediction_id=p.id) for p in predictions
            ])
        return manifest, predictions, review

    def validate(self, review, manifest, predictions, previous):
        if review.image_sha256 != manifest['image_sha256']:
            raise HTTPException(409, 'Empreinte de l’image différente')
        if review.revision != previous.revision:
            raise HTTPException(409, 'Modifié dans un autre onglet. Recharger avant de poursuivre.')
        ids = [a.id for a in review.annotations]
        sources = [a.source_prediction_id for a in review.annotations if a.source_prediction_id]
        if len(ids) != len(set(ids)) or len(sources) != len(set(sources)):
            raise HTTPException(422, 'Identifiants dupliqués')
        if set(sources) != {p.id for p in predictions}:
            raise HTTPException(422, 'Chaque prédiction doit rester traçable, même supprimée')
        previous_sources = {a.source_prediction_id: a.id for a in previous.annotations if a.source_prediction_id}
        for a in review.annotations:
            if a.source_prediction_id and a.id != previous_sources[a.source_prediction_id]:
                raise HTTPException(422, 'Identifiant source modifié')
            x1, y1, x2, y2 = a.bbox
            if not (0 <= x1 < x2 <= manifest['width'] and 0 <= y1 < y2 <= manifest['height']):
                raise HTTPException(422, 'Boîte hors image ou vide')
            if review.status == 'validated' and not a.deleted:
                if not all(a.reviewed.model_dump().values()) or a.gender is None or a.age_range is None:
                    raise HTTPException(422, 'Relire chaque boîte, genre et tranche d’âge')
        if review.status == 'validated' and not review.complete:
            raise HTTPException(422, 'Confirmer la relecture complète de l’affiche')

    def save(self, poster_id, review):
        path = self.folder(poster_id)
        with self.locked(path):
            manifest, predictions, previous = self.load(poster_id)
            # Une modification d'une référence approuvée impose une nouvelle validation.
            if previous.status == 'validated' and (review.annotations != previous.annotations or review.annotator != previous.annotator):
                review.status = 'draft'
                review.complete = False
            self.validate(review, manifest, predictions, previous)
            review.revision += 1
            review.updated_at = datetime.now(timezone.utc).isoformat()
            (path / 'reference.json').unlink(missing_ok=True)
            atomic_json(path / 'review.json', review.model_dump())
        return review

    def export(self, poster_id):
        path = self.folder(poster_id)
        with self.locked(path):
            manifest, predictions, review = self.load(poster_id)
            if review.status != 'validated':
                raise HTTPException(409, 'Affiche non validée')
            self.validate(review, manifest, predictions, review)
            original = {p.id: p for p in predictions}
            counts = dict(validated=0, corrected=0, deleted=0, added=0)
            for a in review.annotations:
                if a.source_prediction_id:
                    p = original[a.source_prediction_id]
                    action = 'deleted' if a.deleted else ('corrected' if any(
                        getattr(a, key) != getattr(p, key) for key in ('bbox', 'gender', 'age_range')
                    ) else 'validated')
                    counts[action] += 1
                elif not a.deleted:
                    counts['added'] += 1
            result = dict(schema_version=1, manifest=manifest, revision=review.revision,
                          annotator=review.annotator, updated_at=review.updated_at,
                          annotations=[a.model_dump() for a in review.annotations if not a.deleted],
                          corrections=counts)
            atomic_json(path / 'reference.json', result)
            return result
