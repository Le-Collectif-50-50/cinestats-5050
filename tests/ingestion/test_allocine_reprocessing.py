"""Reprise des correspondances corrigées, sans accès à Allociné."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import test_allocine_posters

from ingestion.scraping.allocine import connector, main
from ingestion.scraping.allocine.connector import AllocineAirbyteSource, ConnectorConfig

database = test_allocine_posters.database


def test_explicit_recovery_with_no_completed_statuses_skips_exclusion_query():
    config = ConnectorConfig.from_dict({"database_url": "postgresql://unused"})
    config.completed_statuses = []
    connection = MagicMock()
    assert AllocineAirbyteSource()._fetch_completed_records(connection, config) == {}
    connection.execute.assert_not_called()


@pytest.mark.parametrize(
    "current_id, previous_id, strategy, pending",
    [
        ("299027", 265786, "provided_allocine_id", True),
        ("299027", 299027, "provided_allocine_id", False),
        (" 299027 ", 299027, "provided_allocine_id", False),
        (None, 299027, "provided_allocine_id", True),
        (None, 299027, "search", False),
        (None, None, "search", False),
        ("299027", None, "search", True),
        ("299027", 299027, "search", False),
        ("299027", 265786, "search", True),
    ],
)
def test_pending_uses_current_allocine_target(monkeypatch, current_id, previous_id, strategy, pending):
    assert bool(pending_rows(monkeypatch, current_id, previous_id, strategy)) is pending


def pending_rows(monkeypatch, current_id, previous_id, strategy,
                 manual_validation=None, previous_status="success"):
    source = AllocineAirbyteSource()
    config = ConnectorConfig.from_dict({"database_url": "postgresql://unused"})
    engine = MagicMock()
    row = {"source_record_id": "144246", "visa_number": "144246", "allocine_id": current_id,
           "manual_validation": manual_validation}
    engine.begin.return_value.__enter__.return_value.execute.return_value = [SimpleNamespace(_mapping=row)]
    monkeypatch.setattr(connector, "create_engine", lambda *a, **kw: engine)
    monkeypatch.setattr(source, "_assert_input_table_exists", lambda *a: None)
    monkeypatch.setattr(source, "_ensure_output_table_exists", lambda *a: None)
    monkeypatch.setattr(source, "_table_exists", lambda *a: False)
    monkeypatch.setattr(source, "_fetch_completed_records", lambda *a: {
        "144246": {"allocine_id": previous_id, "match_strategy": strategy,
                   "scrape_status": previous_status}
    })
    return source._fetch_pending_rows(config)


@pytest.mark.parametrize("status", ["visa_mismatch", "needs_review"])
@pytest.mark.parametrize("validation, expected", [
    (True, True), ("TRUE", True), (" VRAI ", True), ("1", True),
    (False, False), ("FALSE", False), ("FAUX", False), ("0", False),
    (None, False), ("", False), ("approved", False),
])
def test_manual_validation_reopens_review_only(monkeypatch, status, validation, expected):
    assert bool(pending_rows(monkeypatch, 111149, 111149, "provided_allocine_id",
                             validation, status)) is expected


@pytest.mark.parametrize("strategy", ["provided_allocine_id", "manual_validation", "search"])
def test_checked_success_is_not_reprocessed(monkeypatch, strategy):
    assert pending_rows(monkeypatch, 111149, 111149, strategy, True, "success") == []


def test_checked_not_found_without_changed_target_is_not_reprocessed(monkeypatch):
    assert pending_rows(monkeypatch, 111149, 111149, "provided_allocine_id", True, "not_found") == []


def test_checked_search_without_provided_id_does_not_reopen_completed_record(monkeypatch):
    assert pending_rows(monkeypatch, None, 111149, "search", True, "visa_mismatch") == []


def test_source_id_cli_preserves_target_and_limit():
    with patch.object(main, "_load_dotenv"), \
            patch.object(main, "_load_json", return_value={}), \
            patch.object(connector, "AllocineAirbyteSource") as source, \
            patch("sys.argv", ["scraper", "sync", "--source-id", "144246", "--limit", "1"]):
        source.return_value.sync_to_postgres.return_value = 1
        assert main.main() == 0
        assert source.return_value.sync_to_postgres.call_args.args[0] == {
            "source_ids": ["144246"], "scrape_limit": 1
        }


def test_postgres_reprocessing_history_and_target_filter(database):
    # Réutilise les tables temporaires isolées des tests du connecteur.
    from sqlalchemy import text

    engine, config, raw = database
    raw.update(input_schema=config.output_schema, input_table="id_matching",
               input_id_column="VISA", input_visa_column="VISA",
               input_title_column="TITRE", input_year_column=None,
               input_allocine_id_column="ID_ALLOCINE", input_allocine_url_column=None,
               source_ids=["144246"], scrape_limit=1)
    source = AllocineAirbyteSource()
    config = ConnectorConfig.from_dict(raw)
    with engine.begin() as conn:
        conn.execute(text('CREATE TEMP TABLE id_matching ("VISA" text, "TITRE" text, "ID_ALLOCINE" text)'))
        conn.execute(text("INSERT INTO id_matching VALUES ('144246','16 levers de soleil','299027'), ('149368','Autre film','265786')"))
        # L'ancien ID terminé ne doit pas bloquer le nouvel ID, même après un échec.
        conn.execute(text("""INSERT INTO allocine_data
            (source_record_id, allocine_id, match_strategy, scrape_status, extracted_at)
            VALUES ('144246',265786,'provided_allocine_id','visa_mismatch','2026-05-28'),
                   ('144246',299027,'provided_allocine_id','error','2026-11-12'),
                   ('149368',265786,'provided_allocine_id','success','2026-05-28')"""))
    assert [r["source_record_id"] for r in source._fetch_pending_rows(config)] == ["144246"]
    with engine.begin() as conn:
        conn.execute(text("""INSERT INTO allocine_data
            (source_record_id, allocine_id, match_strategy, scrape_status, extracted_at)
            VALUES ('144246',299027,'provided_allocine_id','success','2026-11-13')"""))
    assert source._fetch_pending_rows(config) == []
    # Un retour vers l'ancien ID se compare au dernier traitement terminé.
    with engine.begin() as conn:
        conn.execute(text('UPDATE id_matching SET "ID_ALLOCINE"=\'265786\' WHERE "VISA"=\'144246\''))
    assert len(source._fetch_pending_rows(config)) == 1


@pytest.mark.parametrize("status", ["visa_mismatch", "needs_review"])
@pytest.mark.parametrize("column_type, checked, unchecked", [
    ("boolean", True, False), ("text", "TRUE", "FALSE"),
])
def test_postgres_manual_retry_stops_after_success(database, status, column_type, checked, unchecked):
    from sqlalchemy import text

    engine, config, raw = database
    raw.update(input_schema=config.output_schema, input_table="id_matching",
               input_id_column="VISA", input_visa_column="VISA", input_title_column="TITRE",
               input_year_column=None, input_allocine_id_column="ID_ALLOCINE",
               input_allocine_url_column=None,
               completed_statuses=["success", "visa_mismatch", "needs_review"])
    config = ConnectorConfig.from_dict(raw)
    source = AllocineAirbyteSource()
    with engine.begin() as conn:
        conn.execute(text(f'''CREATE TEMP TABLE id_matching (
            "VISA" text, "TITRE" text, "ID_ALLOCINE" text, "VALIDATION_MANUELLE" {column_type})'''))
        conn.execute(text('INSERT INTO id_matching VALUES (\'111392\',\'Bamako\',\'111149\',:flag)'),
                     {"flag": unchecked})
        conn.execute(text('''INSERT INTO allocine_data
            (source_record_id, visa_number, allocine_id, match_strategy, scrape_status, extracted_at)
            VALUES ('111392','111392',111149,'provided_allocine_id',:status,'2026-11-12')'''),
                     {"status": status})
    assert source._fetch_pending_rows(config) == []
    with engine.begin() as conn:
        conn.execute(text('UPDATE id_matching SET "VALIDATION_MANUELLE"=:flag'), {"flag": checked})
    rows = source._fetch_pending_rows(config)
    assert len(rows) == 1
    assert connector._is_manually_validated(rows[0])
    with engine.begin() as conn:
        # Une erreur technique sur la reprise ne consomme pas la validation.
        conn.execute(text('''INSERT INTO allocine_data
            (source_record_id, allocine_id, match_strategy, scrape_status, extracted_at)
            VALUES ('111392',111149,'provided_allocine_id','error','2026-11-13')'''))
    assert len(source._fetch_pending_rows(config)) == 1
    with engine.begin() as conn:
        conn.execute(text('''INSERT INTO allocine_data
            (source_record_id, visa_number, allocine_visa_number, allocine_id,
             match_strategy, scrape_status, extracted_at)
            VALUES ('111392','111392','999999',111149,'manual_validation','success','2026-11-14')'''))
    assert source._fetch_pending_rows(config) == []
    assert source._fetch_pending_rows(config) == []
    with engine.begin() as conn:
        assert conn.execute(text('SELECT count(*) FROM allocine_data')).scalar_one() == 3
        assert tuple(conn.execute(text("SELECT visa_number, allocine_visa_number FROM allocine_data WHERE scrape_status='success'")).one()) == ("111392", "999999")
