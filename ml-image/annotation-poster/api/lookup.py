"""Accès optionnel PostgreSQL en lecture seule, sans importer l'application RIC."""
import os
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def find_poster(allocine_id):
    url = os.getenv('ANNOTATION_DATABASE_URL')
    if not url:
        raise HTTPException(503, 'Recherche en base non configurée. Les affiches locales restent disponibles.')
    engine = None
    try:
        engine = create_engine(url, connect_args={'connect_timeout': 5}, pool_pre_ping=True)
        with engine.connect() as connection, connection.begin():
            connection.execute(text('SET TRANSACTION READ ONLY'))
            connection.execute(text("SET LOCAL statement_timeout = '5s'"))
            films = connection.execute(text('SELECT id, original_name FROM public.ric_films WHERE allocine_id = :id LIMIT 2'), {'id': allocine_id}).mappings().all()
            if not films:
                raise HTTPException(404, 'Film absent de la base')
            if len(films) > 1:
                raise HTTPException(409, 'Plusieurs films portent cet identifiant Allociné')
            film = films[0]
            posters = connection.execute(text('SELECT image_base64 FROM public.ric_posters WHERE film_id = :id ORDER BY id LIMIT 2'), {'id': film['id']}).scalars().all()
            if not posters:
                raise HTTPException(404, 'Aucune affiche pour ce film')
            if len(posters) > 1:
                raise HTTPException(409, 'Plusieurs affiches disponibles ; importer celle choisie localement')
            return dict(film_id=film['id'], title=film['original_name'], poster_url=posters[0])
    except SQLAlchemyError:
        raise HTTPException(503, 'Base indisponible ou configuration invalide') from None
    finally:
        if engine is not None:
            engine.dispose()


def download_image(url):
    allowed = os.getenv('ANNOTATION_IMAGE_HOSTS', 'fr.web.img5.acsta.net,fr.web.img6.acsta.net,fr.web.img4.acsta.net').split(',')
    # Liste exacte d'hôtes approuvés côté serveur, aucun proxy d'URL arbitraire.
    with httpx.Client(timeout=20, follow_redirects=False) as client:
        for _ in range(4):
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname not in allowed or parsed.username or parsed.port not in (None, 443):
                raise HTTPException(422, 'URL d’affiche non prise en charge ou hôte non autorisé')
            try:
                with client.stream('GET', url) as response:
                    if response.is_redirect:
                        from urllib.parse import urljoin
                        url = urljoin(url, response.headers['location'])
                        continue
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 20 * 1024 * 1024:
                            raise HTTPException(422, 'Image trop volumineuse (20 Mo maximum)')
                        chunks.append(chunk)
                    return b''.join(chunks)
            except (httpx.HTTPError, KeyError):
                raise HTTPException(502, 'Téléchargement de l’affiche impossible') from None
    raise HTTPException(502, 'Trop de redirections pour l’affiche')
