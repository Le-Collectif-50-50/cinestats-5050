"""Reprise des correspondances corrigées, sans accès à Allociné."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from test_allocine_posters import database  # noqa: F401

from ingestion.scraping.allocine import connector, main
from ingestion.scraping.allocine.connector import AllocineAirbyteSource, ConnectorConfig


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
    source = AllocineAirbyteSource()
    config = ConnectorConfig.from_dict({"database_url": "postgresql://unused"})
    engine = MagicMock()
    row = {"source_record_id": "144246", "visa_number": "144246", "allocine_id": current_id}
    engine.begin.return_value.__enter__.return_value.execute.return_value = [SimpleNamespace(_mapping=row)]
    monkeypatch.setattr(connector, "create_engine", lambda *a, **kw: engine)
    monkeypatch.setattr(source, "_assert_input_table_exists", lambda *a: None)
    monkeypatch.setattr(source, "_ensure_output_table_exists", lambda *a: None)
    monkeypatch.setattr(source, "_table_exists", lambda *a: False)
    monkeypatch.setattr(source, "_fetch_completed_records", lambda *a: {
        "144246": {"allocine_id": previous_id, "match_strategy": strategy}
    })
    assert bool(source._fetch_pending_rows(config)) is pending


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
