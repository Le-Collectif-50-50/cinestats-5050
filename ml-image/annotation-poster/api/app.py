"""API locale activée explicitement ; aucune écriture dans PostgreSQL."""
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from PIL import UnidentifiedImageError

from .importer import prepare
from .lookup import download_image, find_poster
from .models import Review
from .store import Store


def create_app(root=None, enabled=None):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    active = enabled if enabled is not None else os.getenv('ANNOTATION_ENABLED') == 'true'
    if not active:
        return app
    store = Store(root or os.getenv('ANNOTATION_DATA_DIR', 'ml-image/annotation-poster/data'))

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/posters')
    def posters():
        result = []
        for folder in sorted(store.root.iterdir()):
            if folder.name.startswith('.') or not folder.is_dir() or folder.is_symlink():
                continue
            manifest, _, review = store.load(folder.name)
            result.append(dict(id=folder.name, title=manifest['title'], status=review.status,
                               allocine_id=manifest.get('allocine_id')))
        return result

    @app.post('/import/allocine/{allocine_id}')
    def import_allocine(allocine_id: int):
        if not 0 < allocine_id < 2**31:
            raise HTTPException(422, 'Identifiant Allociné invalide')
        # Réutiliser une préparation avec prédictions, sans toucher à la relecture.
        candidates = [p for p in posters() if p['allocine_id'] == allocine_id]
        if len(candidates) == 1:
            return {'id': candidates[0]['id']}
        if len(candidates) > 1:
            raise HTTPException(409, 'Plusieurs préparations locales : choisir dans la liste')
        film = find_poster(allocine_id)
        poster_id = f'allocine-{allocine_id}'
        try:
            prepare(store.root, poster_id, download_image(film['poster_url']), [],
                    dict(film, allocine_id=allocine_id, prediction_stage='none', run_id=None,
                         code_version=None, weights=None, parameters=None))
        except FileExistsError:
            raise HTTPException(409, 'Affiche déjà importée ; recharger la liste') from None
        except (UnidentifiedImageError, ValueError, OSError):
            raise HTTPException(422, 'Contenu téléchargé non reconnu comme image valide') from None
        return {'id': poster_id}

    @app.get('/posters/{poster_id}')
    def detail(poster_id: str):
        manifest, predictions, review = store.load(poster_id)
        return dict(manifest=manifest, predictions=predictions, review=review)

    @app.get('/posters/{poster_id}/image')
    def image(poster_id: str):
        store.load(poster_id)
        return FileResponse(store.folder(poster_id) / 'image.jpg', media_type='image/jpeg')

    @app.put('/posters/{poster_id}/review')
    def save(poster_id: str, review: Review):
        return store.save(poster_id, review)

    @app.get('/posters/{poster_id}/export')
    def export(poster_id: str):
        return JSONResponse(store.export(poster_id), headers={
            'Content-Disposition': f'attachment; filename="{poster_id}-reference.json"',
            'Cache-Control': 'no-store',
        })

    return app


app = create_app()
