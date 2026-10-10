import copy
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.app import create_app
from api.importer import prepare


def image_bytes():
    stream = io.BytesIO()
    Image.new('RGB', (100, 150), '#abcdef').save(stream, format='JPEG')
    return stream.getvalue()


@pytest.fixture
def client(tmp_path):
    prepare(tmp_path, 'sample', image_bytes(), [dict(id='p1', bbox=[10, 20, 40, 60], gender='female', age_range='70+')],
            dict(title='Fixture', allocine_id=123, prediction_stage='filtered'))
    return TestClient(create_app(tmp_path, True))


def reviewed(client):
    r = client.get('/posters/sample').json()['review']
    r['annotations'][0]['reviewed'] = dict(bbox=True, gender=True, age_range=True)
    r.update(status='validated', complete=True)
    return r


def test_validation_export_and_invalidation(client):
    original = client.get('/posters/sample').json()['predictions']
    r = reviewed(client)
    assert client.put('/posters/sample/review', json=r).status_code == 200
    export = client.get('/posters/sample/export').json()
    assert export['annotations'][0]['age_range'] == '70+'
    assert export['corrections']['validated'] == 1
    r = client.get('/posters/sample').json()['review']
    r['annotations'][0]['gender'] = 'unknown'
    result = client.put('/posters/sample/review', json=r).json()
    assert result['status'] == 'draft'
    assert client.get('/posters/sample/export').status_code == 409
    assert client.get('/posters/sample').json()['predictions'] == original


def test_conflict_and_field_review(client):
    stale = reviewed(client)
    incomplete = copy.deepcopy(stale)
    incomplete['annotations'][0]['reviewed']['age_range'] = False
    assert client.put('/posters/sample/review', json=incomplete).status_code == 422
    incomplete['annotations'][0]['reviewed']['age_range'] = True
    incomplete['annotations'][0]['age_range'] = None
    assert client.put('/posters/sample/review', json=incomplete).status_code == 422
    assert client.put('/posters/sample/review', json=stale).status_code == 200
    assert client.put('/posters/sample/review', json=stale).status_code == 409


def test_delete_add_unknown_and_empty_reference(client):
    r = reviewed(client)
    r['annotations'][0]['deleted'] = True
    added = copy.deepcopy(r['annotations'][0])
    added.update(id='manual', source_prediction_id=None, deleted=False, age_range='unknown', gender='unknown')
    r['annotations'].append(added)
    assert client.put('/posters/sample/review', json=r).status_code == 200
    out = client.get('/posters/sample/export').json()
    assert len(out['annotations']) == 1
    assert out['corrections'] == dict(validated=0, corrected=0, deleted=1, added=1)
    r = client.get('/posters/sample').json()['review']
    r['annotations'][1]['deleted'] = True
    r = client.put('/posters/sample/review', json=r).json()
    r.update(status='validated', complete=True)
    client.put('/posters/sample/review', json=r)
    assert client.get('/posters/sample/export').json()['annotations'] == []


def test_bounds_traceability_and_checksum(client):
    r = reviewed(client)
    r['annotations'][0]['bbox'][2] = 500
    assert client.put('/posters/sample/review', json=r).status_code == 422
    r = reviewed(client)
    r['annotations'] = []
    assert client.put('/posters/sample/review', json=r).status_code == 422
    r = reviewed(client)
    r['image_sha256'] = 'changed'
    assert client.put('/posters/sample/review', json=r).status_code == 409
    assert client.get('/posters/not_present').status_code == 404


def test_disabled_and_empty(tmp_path):
    assert TestClient(create_app(tmp_path, False)).get('/posters').status_code == 404
    prepare(tmp_path, 'empty', image_bytes(), [], dict(title='Sans visage', prediction_stage='none'))
    c = TestClient(create_app(tmp_path, True))
    r = c.get('/posters/empty').json()['review']
    r.update(status='validated', complete=True)
    assert c.put('/posters/empty/review', json=r).status_code == 200
    assert c.get('/posters/empty/export').json()['annotations'] == []


def test_allocine_reuses_local_without_database(client, monkeypatch):
    monkeypatch.delenv('ANNOTATION_DATABASE_URL', raising=False)
    assert client.post('/import/allocine/123').json() == {'id': 'sample'}
    assert client.post('/import/allocine/456').status_code == 503
    assert client.post('/import/allocine/0').status_code == 422


def test_allocine_import_and_no_overwrite(client, monkeypatch):
    monkeypatch.setattr('api.app.find_poster', lambda _: dict(film_id=10, title='Film', poster_url='https://example.test/image'))
    monkeypatch.setattr('api.app.download_image', lambda _: image_bytes())
    response = client.post('/import/allocine/456')
    assert response.status_code == 200
    assert client.get('/posters/allocine-456').json()['manifest']['prediction_stage'] == 'none'
    r = client.get('/posters/allocine-456').json()['review']
    r['annotator'] = 'Test humain'
    client.put('/posters/allocine-456/review', json=r)
    client.post('/import/allocine/456')
    assert client.get('/posters/allocine-456').json()['review']['annotator'] == 'Test humain'


def test_mutated_image_rejected(tmp_path):
    prepare(tmp_path, 'sample', image_bytes(), [], dict(title='Fixture'))
    (tmp_path / 'sample/image.jpg').write_bytes(b'changed')
    assert TestClient(create_app(tmp_path, True)).get('/posters/sample').status_code == 409


def test_converter_and_pipeline_export(tmp_path, monkeypatch):
    import importlib.util
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from api.importer import convert_predictions
    predictions = [dict(bbox=[10, 20, 40, 60], gender='Female', age='70+', conf=0.8)]
    assert convert_predictions(predictions)[0]['gender'] == 'female'
    module_path = Path(__file__).resolve().parents[2] / 'scripts/annotation_export.py'
    spec = importlib.util.spec_from_file_location('annotation_export', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image = tmp_path / 'source.jpg'
    image.write_bytes(image_bytes())
    monkeypatch.setenv('ANNOTATION_EXPORT_DIR', str(tmp_path / 'out'))
    monkeypatch.setenv('ANNOTATION_RUN_ID', 'fixture')
    module.export_annotation(image, predictions,
        SimpleNamespace(allocine_id=123, visa_number=456, poster_url='local'),
        SimpleNamespace(source='fixture.csv'))
    folder = tmp_path / 'out/allocine-123'
    assert json.loads((folder / 'predictions.json').read_text())[0]['age_range'] == '70+'
    assert json.loads((folder / 'manifest.json').read_text())['prediction_stage'] == 'filtered'
    assert image.exists()
