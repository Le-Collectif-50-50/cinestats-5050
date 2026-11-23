"""Tests d'identité, de sélection et de routage sans réseau ni base réelle."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest

from ingestion.scraping.browser import WebsiteBlockedError
from ingestion.scraping.id_matching.__main__ import references
from ingestion.scraping.id_matching.identity import Film, assess, parse_film, title_norm
from ingestion.scraping.id_matching.matching import match
from ingestion.scraping.id_matching.store import destination, save_result


@pytest.fixture
def reference():
    return Film("cnc", "149572", "Desrances", ["Apolline TRAORE"], visa="149572")


def test_identity_requires_title_and_director(reference):
    candidate = Film("tmdb", "627067", "Desrances", ["TRAORÉ Apolline"])
    assert assess(reference, candidate)[0] == "confirme"
    assert assess(reference, replace(candidate, directors=[]))[0] == "a_revoir"
    assert (
        assess(reference, replace(candidate, directors=["Autre personne"]))[0] == "incompatible"
    )
    assert assess(reference, replace(candidate, title="Un autre film"))[0] != "confirme"
    assert title_norm("Filles d’Abraham (Les)") == title_norm("Les Filles d'Abraham")


@pytest.mark.parametrize("key", ["film", "initFilm"])
def test_mubi_uses_numeric_id(key):
    html = '<script id="__NEXT_DATA__">{"props":{"pageProps":{"KEY":{"id":243777,"title":"Desrances","directors":[{"name":"Apolline Traoré"}]}}}}</script>'
    film = parse_film("mubi", html.replace("KEY", key), "https://mubi.com/fr/films/desrances")
    assert film.id == "243777"
    with pytest.raises(ValueError):
        parse_film("mubi", "<h1>Desrances</h1>", film.url)


def test_tmdb_ignores_non_director_credits():
    html = '<section class="header"><div class="title"><h2><a>Desrances</a></h2></div><ol class="people"><li class="profile"><a>Apolline Traoré</a><p class="character">Director</p></li><li class="profile"><a>Autre personne</a><p class="character">Writer</p></li></ol></section>'
    film = parse_film("tmdb", html, "https://www.themoviedb.org/movie/627067-desrances")
    assert film.id == "627067" and film.directors == ["Apolline Traoré"]


def test_tmdb_original_title_never_reads_next_fact():
    html = '<section class="facts"><p><strong><bdi>Titre d’origine</bdi></strong> Desrances</p><p><strong>Statut</strong> Film sorti</p></section><section class="header"><div class="title"><h2><a>Desrances</a></h2></div></section>'
    film = parse_film("tmdb", html, "https://www.themoviedb.org/movie/627067")
    assert film.aliases == ["Desrances"]


def test_select_only_missing_ids_and_preserve_existing():
    rows = [
        {"VISA": "1", "TITRE": "Film", "ID_MUBI": "123", "ID_TMDB": " "},
        {"VISA": "2", "TITRE": "Film 2", "ID_MUBI": None, "ID_TMDB": "0"},
    ]
    films = [{"VISA": 1, "REALISATEUR": "Nom Prénom"}]
    items = list(references(rows, films, ("mubi", "tmdb")))
    assert items[0][1] == ["tmdb"] and items[1][1] == ["mubi"]
    assert not items[1][0].directors


def test_duplicate_visa_conflicts_not_confirmable():
    rows = [{"VISA": "1", "TITRE": "Film"}, {"VISA": "1", "TITRE": "Autre"}]
    films = [{"VISA": "1", "REALISATEUR": "Nom"}, {"VISA": "1", "REALISATEUR": "Autre"}]
    ref, _ = next(references(rows, films, ("tmdb",)))
    assert not ref.title and not ref.directors
    rows[1]["ID_TMDB"] = "123"
    assert list(references(rows, films, ("tmdb",))) == []


class Browser:
    def __init__(self, count=1, broken=False, blocked=False):
        self.count, self.broken, self.blocked = count, broken, blocked
        self.page = SimpleNamespace(url="")

    async def fetch_html(self, url):
        self.page.url = url
        if self.blocked:
            raise WebsiteBlockedError("HTTP 403")
        if "/search/" in url:
            return (
                '<div class="search_results">'
                + "".join(
                    f'<a href="/movie/{n}">Desrances</a>' for n in range(1, self.count + 1)
                )
                + "</div>"
            )
        if self.broken and url.endswith("/2"):
            raise ValueError("Fiche illisible")
        return '<script type="application/ld+json">{"@type":"Movie","name":"Desrances","director":{"name":"Apolline Traoré"}}</script>'


@pytest.mark.parametrize(
    "count,broken,limit,status",
    [
        (1, False, 10, "trouve"),
        (2, False, 10, "ambigu"),
        (2, True, 10, "a_revoir"),
        (2, False, 1, "a_revoir"),
    ],
)
def test_unique_complete_search_required(reference, count, broken, limit, status):
    result = asyncio.run(match(Browser(count, broken), reference, "tmdb", max_candidates=limit))
    assert result["status"] == status
    assert bool(result["confirmed_id"]) == (status == "trouve")
    assert destination(result) == (
        "id_matching_confirmed" if status == "trouve" else "id_matching_review"
    )


def test_blocked_is_review(reference):
    result = asyncio.run(match(Browser(blocked=True), reference, "tmdb"))
    assert result["status"] == "bloque"
    assert destination(result) == "id_matching_review"


def test_missing_director_needs_no_network(reference):
    result = asyncio.run(match(None, replace(reference, directors=[]), "mubi"))
    assert result["status"] == "a_revoir"


def test_no_search_results_not_unknown_page(reference):
    class Empty(Browser):
        async def fetch_html(self, url):
            self.page.url = url
            return "<p>No results</p>"

    assert asyncio.run(match(Empty(), reference, "tmdb"))["status"] == "non_trouve"
    assert asyncio.run(match(Browser(count=0), reference, "tmdb"))["status"] == "erreur"


def test_invalid_confirmation_rejected():
    with pytest.raises(ValueError):
        destination({"status": "trouve", "confirmed_id": "some-slug"})
    with pytest.raises(ValueError):
        destination({"status": "ambigu", "confirmed_id": "123"})


def test_persistence_uses_only_ops_and_preserves_evidence(reference):
    result = asyncio.run(match(Browser(), reference, "tmdb"))

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, query, params):
            assert "INSERT INTO ops.id_matching_confirmed" in str(query)
            assert params["proposed_id"] == "1"
            assert '"candidates"' in params["evidence"]

    save_result(SimpleNamespace(begin=Connection), uuid4(), result)
