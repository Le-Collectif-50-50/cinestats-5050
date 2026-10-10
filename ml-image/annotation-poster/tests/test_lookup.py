from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from api import lookup


class Result:
    def __init__(self, rows):
        self.rows = rows
    def mappings(self):
        return self
    def scalars(self):
        return self
    def all(self):
        return self.rows


@pytest.mark.parametrize('films,posters,status', [
    ([], [], 404),
    ([{'id': 1}, {'id': 2}], [], 409),
    ([{'id': 1, 'original_name': 'Film'}], [], 404),
    ([{'id': 1, 'original_name': 'Film'}], ['url1', 'url2'], 409),
    ([{'id': 1, 'original_name': 'Film'}], ['https://fr.web.img5.acsta.net/poster.jpg'], 200),
])
def test_read_only_parameterized_lookup(monkeypatch, films, posters, status):
    queries = []
    class Connection:
        def begin(self):
            return nullcontext()
        def execute(self, sql, params=None):
            queries.append((str(sql), params))
            return Result(films if 'ric_films' in str(sql) else posters)
    class Engine:
        def connect(self):
            return nullcontext(Connection())
        def dispose(self):
            pass
    monkeypatch.setenv('ANNOTATION_DATABASE_URL', 'postgresql+psycopg://fake')
    monkeypatch.setattr(lookup, 'create_engine', lambda *a, **kw: Engine())
    if status == 200:
        assert lookup.find_poster(123)['title'] == 'Film'
    else:
        with pytest.raises(HTTPException) as e:
            lookup.find_poster(123)
        assert e.value.status_code == status
    assert queries[0][0] == 'SET TRANSACTION READ ONLY'
    assert queries[2][1] == {'id': 123}


def test_refuse_arbitrary_media_host():
    with pytest.raises(HTTPException) as e:
        lookup.download_image('http://127.0.0.1/private')
    assert e.value.status_code == 422
