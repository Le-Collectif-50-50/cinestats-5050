import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text

from ingestion.scraping.allocine import connector, poster_backfill
from ingestion.scraping.allocine.allocine_scraper import AllocineScraper
from ingestion.scraping.allocine.connector import AllocineAirbyteSource, ConnectorConfig
from ingestion.scraping.allocine.main import DEFAULT_ENV_PATH, _load_dotenv, _load_json

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"
POSTER = "https://images.example.test/affiche.jpg"
MIGRATION = ROOT / "infra/data/2026-10-15-allocine-poster-url.sql"


class FixtureSession:
    calls = []
    pages = {}

    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def fetch_html(self, url):
        self.calls.append(url)
        page = self.pages.get(url, "allocine_poster.html")
        if isinstance(page, Exception):
            raise page
        return (FIXTURES / page).read_text()


@pytest.fixture(autouse=True)
def fake_browser(monkeypatch):
    FixtureSession.calls = []
    FixtureSession.pages = {}
    monkeypatch.setattr(
        AllocineAirbyteSource,
        "_load_scraping_dependencies",
        lambda self: (AllocineScraper(), FixtureSession),
    )
    # Aucun test ne peut ouvrir un navigateur réel, même par inadvertance.
    from ingestion.scraping import browser

    monkeypatch.setattr(browser, "AsyncBrowserSession", FixtureSession)


@pytest.mark.parametrize(
    "fixture, expected", [("allocine_poster.html", POSTER), ("allocine_no_poster.html", None)]
)
def test_extract(fixture, expected):
    assert (
        AllocineScraper().extract_film_details((FIXTURES / fixture).read_text())["poster_url"]
        == expected
    )


def test_image_without_src():
    assert (
        AllocineScraper().extract_film_details(
            '<div class="entity-card"><img class="thumbnail-img"></div>'
        )["poster_url"]
        is None
    )


@pytest.fixture
def database(monkeypatch):
    if os.getenv("RIC_POSTER_TEST_DB") != "1":
        pytest.skip(
            "RIC_POSTER_TEST_DB=1 autorise les tables temporaires sur la base ingestion/.env"
        )
    _load_dotenv(DEFAULT_ENV_PATH)
    raw = _load_json(str(ROOT / "ingestion/scraping/allocine/config.json"))
    config = ConnectorConfig.from_dict(raw)
    engine = create_engine(
        config.database_url, pool_size=1, max_overflow=0, connect_args={"connect_timeout": 10}
    )
    try:
        # Relations temporaires uniquement, aucune lecture/écriture des tables métier.
        with engine.begin() as conn:
            conn.execute(text("CREATE TEMP TABLE poster_test_anchor (id int)"))
            schema = conn.execute(
                text("SELECT nspname FROM pg_namespace WHERE oid = pg_my_temp_schema()")
            ).scalar_one()
        raw.update(
            output_schema=schema,
            output_table="allocine_data",
            inter_film_delay_min_seconds=0,
            inter_film_delay_max_seconds=0,
        )
        config = ConnectorConfig.from_dict(raw)
        proxy = SimpleNamespace(
            begin=engine.begin, connect=engine.connect, dispose=lambda: None
        )
        monkeypatch.setattr(connector, "create_engine", lambda *a, **k: proxy)
        monkeypatch.setattr(poster_backfill, "create_engine", lambda *a, **k: proxy)
        with engine.begin() as conn:
            AllocineAirbyteSource()._ensure_output_table_exists(conn, config)
        yield engine, config, raw
    finally:
        engine.dispose()


def migrate(conn, config):
    # Exactement le SQL versionné, avec substitution du seul schéma cible.
    sql = MIGRATION.read_text().replace("raw.", f'"{config.output_schema}".')
    for statement in sql.split(";"):
        # BEGIN/COMMIT sont gérés par engine.begin() dans le test.
        lines = [line for line in statement.splitlines() if not line.strip().startswith("--")]
        statement = "\n".join(lines).strip()
        if statement and statement not in {"BEGIN", "COMMIT"}:
            conn.execute(text(statement))


def record(source_id="123", allocine_id=1, fixture="allocine_poster.html"):
    FixtureSession.pages[
        AllocineScraper.FILM_URL.format(allocine_film_id=allocine_id)
    ] = fixture
    return asyncio.run(
        AllocineAirbyteSource()._scrape_one_record(
            "initial-run",
            FixtureSession(),
            AllocineScraper(),
            {
                "source_record_id": source_id,
                "visa_number": "123",
                "original_name": "Film test",
                "allocine_id": allocine_id,
            },
        )
    )


def rows(engine, config):
    with engine.connect() as conn:
        return [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    f'SELECT * FROM "{config.output_schema}".allocine_data ORDER BY source_record_id, allocine_id'
                )
            )
        ]


def test_contract_and_timeout():
    schema = AllocineAirbyteSource().discover()["streams"][0]["json_schema"]
    assert schema["properties"]["poster_url"]["type"] == ["string", "null"]
    result = AllocineAirbyteSource()._build_timeout_error_record(
        "run", {"source_record_id": "1"}, 1
    )
    assert result["poster_url"] is None


@pytest.mark.parametrize(
    "fixture, expected", [("allocine_poster.html", POSTER), ("allocine_no_poster.html", None)]
)
def test_propagation_sql(database, fixture, expected):
    engine, config, _ = database
    result = record(fixture=fixture)
    assert result["scrape_status"] == "success"
    assert result["poster_url"] == expected
    AllocineAirbyteSource()._insert_records(config, [result])
    assert rows(engine, config)[0]["poster_url"] == expected


def test_migration_existing_table_replay(database):
    engine, config, _ = database
    AllocineAirbyteSource()._insert_records(config, [record()])
    with engine.begin() as conn:
        conn.execute(
            text(f'ALTER TABLE "{config.output_schema}".allocine_data DROP COLUMN poster_url')
        )
        migrate(conn, config)
        migrate(conn, config)
    result = rows(engine, config)[0]
    assert result["poster_url"] is None
    assert result["original_name"] == "Film test"
    with engine.begin() as conn:
        conn.execute(
            text(f'UPDATE "{config.output_schema}".allocine_data SET poster_url = :url'),
            {"url": POSTER},
        )
        migrate(conn, config)
    assert rows(engine, config)[0]["poster_url"] == POSTER


def test_backfill_selection_resume_and_preservation(database):
    engine, config, raw = database
    records = [record(str(i), i) for i in range(1, 6)]
    for item in records[:4]:
        item["poster_url"] = None
    records[3]["scrape_status"] = "error"
    AllocineAirbyteSource()._insert_records(config, records)
    with engine.begin() as conn:
        migrate(conn, config)
    before = rows(engine, config)
    FixtureSession.calls.clear()
    selected = poster_backfill.backfill_posters(raw, dry_run=True, limit=2)
    assert [row["source_record_id"] for row in selected] == ["1", "2"]
    assert FixtureSession.calls == []
    assert rows(engine, config) == before
    assert poster_backfill.backfill_posters(raw, dry_run=True, source_ids=["3", "5"]) == [
        {"source_record_id": "3", "allocine_id": 3}
    ]
    FixtureSession.pages[
        AllocineScraper.FILM_URL.format(allocine_film_id=2)
    ] = "allocine_no_poster.html"
    FixtureSession.pages[AllocineScraper.FILM_URL.format(allocine_film_id=3)] = RuntimeError(
        "fixture failure"
    )
    result = poster_backfill.backfill_posters(raw, limit=3)
    assert [r["status"] for r in result] == ["updated", "missing", "error"]
    after = rows(engine, config)
    for original, updated in zip(before, after, strict=True):
        assert {k: v for k, v in original.items() if k != "poster_url"} == {
            k: v for k, v in updated.items() if k != "poster_url"
        }
    assert after[4]["poster_url"] == POSTER
    assert after[3]["poster_url"] is None
    assert [
        r["source_record_id"] for r in poster_backfill.backfill_posters(raw, dry_run=True)
    ] == ["2", "3"]
    FixtureSession.pages.clear()
    assert all(r["status"] == "updated" for r in poster_backfill.backfill_posters(raw))
    assert poster_backfill.backfill_posters(raw, dry_run=True) == []
    with engine.connect() as conn:
        assert (
            conn.execute(
                text(
                    f'SELECT count(*) FROM "{config.output_schema}".allocine_data_poster_backfill'
                )
            ).scalar_one()
            == 5
        )


def test_concurrent_url_preserved(database):
    engine, config, _ = database
    AllocineAirbyteSource()._insert_records(config, [record()])
    with engine.begin() as conn:
        migrate(conn, config)
        result = poster_backfill.save_attempt(
            conn,
            config,
            dict(
                run_id="backfill",
                source_record_id="123",
                allocine_id=1,
                source_url="https://www.allocine.fr/film/fichefilm_gen_cfilm=1.html",
                poster_url="https://images.example.test/other.jpg",
                status="missing",
                error_message=None,
            ),
        )
    assert result["status"] == "unchanged"
    assert rows(engine, config)[0]["poster_url"] == POSTER


def test_staging_sql(database):
    import yaml

    engine, config, _ = database
    AllocineAirbyteSource()._insert_records(
        config, [record("1", 1), record("2", 2, "allocine_no_poster.html")]
    )
    model = ROOT / "ingestion/dbt/models/staging/stg_allocine_films.sql"
    sql = "SELECT" + model.read_text().split("SELECT", 1)[1]
    sql = sql.replace(
        "{{ source('raw', 'allocine_data') }}", f'"{config.output_schema}".allocine_data'
    )
    with engine.connect() as conn:
        result = [dict(row._mapping) for row in conn.execute(text(sql))]
    assert {r["source_record_id"]: r["poster_url"] for r in result} == {1: POSTER, 2: None}
    models = yaml.safe_load((ROOT / "ingestion/dbt/models/models.yml").read_text())["models"]
    staging = next(m for m in models if m["name"] == "stg_allocine_films")
    assert any(c["name"] == "poster_url" for c in staging["columns"])


def test_backfill_sql_error_rolls_back_and_continues(database, monkeypatch):
    engine, config, raw = database
    records = [record(str(i), i, "allocine_no_poster.html") for i in (1, 2)]
    AllocineAirbyteSource()._insert_records(config, records)
    with engine.begin() as conn:
        migrate(conn, config)
    FixtureSession.pages.clear()
    save = poster_backfill.save_attempt

    def fail_first(connection, config, attempt):
        result = save(connection, config, attempt)
        if attempt["source_record_id"] == "1":
            raise RuntimeError("fixture SQL rollback")
        return result

    monkeypatch.setattr(poster_backfill, "save_attempt", fail_first)
    result = poster_backfill.backfill_posters(raw)
    assert [r["status"] for r in result] == ["error", "updated"]
    assert [r["poster_url"] for r in rows(engine, config)] == [None, POSTER]
    with engine.connect() as conn:
        assert (
            conn.execute(
                text(
                    f'SELECT count(*) FROM "{config.output_schema}".allocine_data_poster_backfill'
                )
            ).scalar_one()
            == 1
        )


def test_export_import_replay(database, monkeypatch, tmp_path):
    from ingestion.scraping.allocine import poster_export

    engine, config, raw = database
    proxy = SimpleNamespace(connect=engine.connect, dispose=lambda: None)
    monkeypatch.setattr(poster_export, "create_engine", lambda *a, **k: proxy)
    original = record()
    original["poster_url"] = None
    AllocineAirbyteSource()._insert_records(config, [original])
    with engine.begin() as conn:
        migrate(conn, config)
        poster_backfill.save_attempt(
            conn,
            config,
            dict(
                run_id="export-test",
                source_record_id="123",
                allocine_id=1,
                source_url="https://www.allocine.fr/film/fichefilm_gen_cfilm=1.html",
                poster_url=POSTER + "?q=';--$poster$",
                status="missing",
                error_message=None,
            ),
        )
    output = tmp_path / "posters.sql"
    assert poster_export.export_posters(raw, output) == 1
    assert poster_export.export_posters(raw, tmp_path / "empty.sql", "absent") == 0
    with pytest.raises(FileExistsError):
        poster_export.export_posters(raw, output)
    sql = output.read_text().replace("raw.", f'"{config.output_schema}".')
    with engine.begin() as conn:
        conn.execute(
            text(f'UPDATE "{config.output_schema}".allocine_data SET poster_url = NULL')
        )
    # L'import effectif utilise son propre BEGIN/COMMIT, comme psql.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(sql)
        conn.exec_driver_sql(sql)
        assert (
            conn.execute(
                text(
                    f'SELECT count(*) FROM "{config.output_schema}".allocine_data_poster_backfill'
                )
            ).scalar_one()
            == 2
        )
    imported = rows(engine, config)[0]
    assert imported["poster_url"] == POSTER + "?q=';--$poster$"
    assert imported["run_id"] == original["run_id"]
    assert imported["record_hash"] == original["record_hash"]


@pytest.mark.parametrize(
    "status, expected_count, expected_status",
    [("missing", 3, "complete"), ("error", 2, "stopped_on_errors")],
)
def test_campaign_bounds_and_checkpoint(
    monkeypatch, tmp_path, status, expected_count, expected_status
):
    from contextlib import nullcontext
    from ingestion.scraping.allocine import poster_campaign

    raw = {"database_url": "postgresql+psycopg://unused/test"}
    engine = SimpleNamespace(connect=lambda: nullcontext(None), dispose=lambda: None)
    monkeypatch.setattr(poster_campaign, "create_engine", lambda *_: engine)
    monkeypatch.setattr(
        poster_campaign,
        "select_candidates",
        lambda *_: [{"source_record_id": str(i), "allocine_id": i} for i in (1, 2, 3)],
    )
    processed = []

    async def fake_process(engine, config, candidates, *args):
        processed.extend(candidates)
        return [{"status": status} for _ in candidates]

    def fake_export(raw, output):
        Path(output).write_text("-- SQL checkpoint\n")
        return 0

    monkeypatch.setattr(poster_campaign, "process_candidates", fake_process)
    monkeypatch.setattr(poster_campaign, "export_posters", fake_export)
    result = poster_campaign.run_campaign(raw, tmp_path / "campaign", batch_size=2)
    assert len(processed) == expected_count
    assert result["status"] == expected_status
    assert (tmp_path / "campaign/posters.sql").exists()
    assert not (tmp_path / "campaign/posters.pending.sql").exists()
