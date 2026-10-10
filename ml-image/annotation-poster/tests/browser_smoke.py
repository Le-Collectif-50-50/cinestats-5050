"""Parcours navigateur sur fixture synthétique ; lancer avec le Compose actif."""
import io
import os
import shutil
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright, expect

from api.importer import prepare


def main():
    root = Path(__file__).resolve().parents[1] / 'data'
    poster_id = 'browser-fixture'
    folder = root / poster_id
    if folder.exists():
        raise RuntimeError('Fixture déjà présente ; vérifier avant de la supprimer')
    stream = io.BytesIO()
    Image.new('RGB', (400, 600), '#716659').save(stream, format='JPEG')
    prepare(root, poster_id, stream.getvalue(), [dict(id='p1', bbox=[40, 50, 140, 200], gender='female', age_range='70+')],
            dict(title='Test navigateur', allocine_id=9999999, prediction_stage='filtered', run_id='test', code_version='fixture'))
    try:
        with sync_playwright() as p:
            executable = os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
            browser = p.chromium.launch(executable_path=executable)
            page = browser.new_page(viewport={'width': 1450, 'height': 1050})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(os.getenv('ANNOTATION_TEST_URL', 'http://127.0.0.1:3010'))
            page.get_by_label('Affiches locales').select_option(poster_id)
            expect(page.get_by_role('heading', name='Test navigateur')).to_be_visible()
            page.get_by_role('button', name='Tout valider pour ce visage').click()
            expect(page.get_by_role('status')).to_contain_text('Sauvegardé')
            page.get_by_label('J’ai relu toute l’affiche et ajouté les visages manqués.').check()
            expect(page.get_by_role('status')).to_contain_text('Sauvegardé')
            page.get_by_role('button', name='Valider l’affiche', exact=True).click()
            expect(page.get_by_role('status')).to_contain_text('Sauvegardé · Validée')
            with page.expect_download() as download:
                page.get_by_role('link', name='Exporter la référence et le bilan').click()
            import json
            exported = json.loads(Path(download.value.path()).read_text())
            assert exported['annotations'][0]['age_range'] == '70+'
            # Une correction invalide la référence ; âge et genre restent indépendants.
            page.get_by_label('Genre perçu', exact=True).select_option('unknown')
            expect(page.get_by_role('status')).to_contain_text('Sauvegardé · Brouillon')
            expect(page.get_by_label('Tranche d’âge apparente', exact=True)).to_have_value('70+')
            page.get_by_role('button', name='Annuler', exact=True).click()
            expect(page.get_by_label('Genre perçu', exact=True)).to_have_value('female')
            page.get_by_role('button', name='Rétablir', exact=True).click()
            expect(page.get_by_label('Genre perçu', exact=True)).to_have_value('unknown')
            expect(page.get_by_role('status')).to_contain_text('Sauvegardé')
            # Ajout au zoom 2 : les coordonnées restent celles de l’image originale.
            page.get_by_label('Zoom', exact=True).fill('2')
            page.get_by_role('button', name='Ajouter un visage', exact=True).click()
            svg = page.get_by_label('Affiche et boîtes des visages')
            rect = svg.bounding_box()
            scale = rect['width'] / 400
            x, y = rect['x'], rect['y']
            page.mouse.move(x + 20 * scale, y + 20 * scale)
            page.mouse.down()
            page.mouse.move(x + 60 * scale, y + 60 * scale, steps=6)
            page.mouse.up()
            expect(page.get_by_label('x1', exact=True)).to_have_value('20')
            expect(page.get_by_label('x2', exact=True)).to_have_value('60')
            page.get_by_label('Genre perçu', exact=True).select_option('unknown')
            page.get_by_label('Tranche d’âge apparente', exact=True).select_option('unknown')
            page.get_by_role('button', name='Supprimer cette détection').click()
            expect(page.get_by_role('button', name='Restaurer ce visage')).to_be_visible()
            page.get_by_role('button', name='Restaurer ce visage').click()
            expect(page.get_by_role('status')).to_contain_text('Sauvegardé')
            page.reload()
            page.get_by_label('Affiches locales').select_option(poster_id)
            expect(page.get_by_role('heading', name='Visages (2)')).to_be_visible()
            page.screenshot(path='/tmp/ric-annotation-poster-browser.png', full_page=True)
            assert not errors, errors
            browser.close()
            print('Parcours navigateur OK : validation, export, correction, annuler/rétablir, ajout au zoom, suppression/restauration, reprise.')
    finally:
        shutil.rmtree(folder)


if __name__ == '__main__':
    main()
