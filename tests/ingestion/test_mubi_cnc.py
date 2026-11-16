"""Contrats Mubi CNC : identité, reprise, ciblage et publication."""
import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import text

from ingestion.prefect import flows
from ingestion.scraping.mubi_cnc import connector as c
from ingestion.scraping.mubi_cnc import main as cli

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("mubi_dashboard", ROOT / "infra/data/metabase-mubi-review.py")
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)


def config(**kwargs):
    return c.ConnectorConfig.from_dict({"database_url": "sqlite://", "inter_request_delay_min_seconds": 0,
                                       "inter_request_delay_max_seconds": 0, **kwargs})


def page(mubi_id=123, awards=None):
    return '<script id="__NEXT_DATA__" type="application/json">' + json.dumps({"props": {"pageProps": {
        "film": {"id": mubi_id, "web_url": "/fr/films/example"}, "awards": [] if awards is None else awards,
    }}}) + '</script>'


@pytest.mark.parametrize("html,expected", [(page(), "no_awards"), ("<html>broken</html>", "error"),
                                         (page(999), "error"), (page(awards=[{"industry_event": {"name": "Cannes", "slug": "cannes", "type": "festival"}, "year": 2024, "full_display_text": "2024 | Lauréat : Prix"}]), "success")])
def test_identity_missing_payload_and_empty_awards(monkeypatch, html, expected):
    engine = MagicMock()
    monkeypatch.setattr(c, "create_engine", lambda *_: engine)
    for name in ("_ensure_schema", "_ensure_festival_films_table", "_ensure_film_awards_table"):
        monkeypatch.setattr(c, name, Mock())
    monkeypatch.setattr(c, "_fetch_pending_mubi_ids", lambda *_: [123])
    browser = AsyncMock()
    browser.__aenter__.return_value = browser
    factory = Mock(return_value=browser)
    monkeypatch.setattr("ingestion.scraping.browser.AsyncBrowserSession", factory)
    source = c.MubiCncAirbyteSource()
    source._fetch_with_retry = AsyncMock(return_value=(html, None))
    source._checkpoint = Mock()
    records, editions = asyncio.run(source._scrape_cnc_film_awards(config()))
    assert records[0]["scrape_status"] == expected
    source._checkpoint.assert_called_once()
    assert factory.call_args.kwargs["lightweight"] is True
    assert factory.call_args.kwargs["navigation_wait_until"] == "domcontentloaded"
    assert editions == ([("cannes", "2024")] if expected == "success" else [])


def test_target_selection_is_bound_and_deduplicates_shared_ids(monkeypatch):
    db = Mock()
    db.execute.return_value.fetchall.return_value = [("00123",), ("123",)]
    monkeypatch.setattr(c, "_fetch_processed_mubi_ids", lambda *_: {123})
    assert c._fetch_pending_mubi_ids(db, config(visa_number="001")) == []
    assert c._fetch_pending_mubi_ids(db, config(visa_number="001", force_rescrape=True)) == [123]
    assert db.execute.call_args.args[1] == {"visa": "001"}
    assert ':visa' in str(db.execute.call_args.args[0])
    db.execute.return_value.fetchall.return_value = [(None,)]
    with pytest.raises(ValueError, match="ID Mubi"):
        c._fetch_pending_mubi_ids(db, config(visa_number="1"))


@pytest.mark.parametrize("kwargs", [{"force_rescrape": True}, {"visa_number": "0"}, {"visa_number": "1;delete"}, {"force_rescrape": "false"}])
def test_reject_invalid_target(kwargs):
    with pytest.raises(ValueError):
        config(**kwargs)


def test_resume_editions_without_new_awards_and_failures_stop_publication(monkeypatch):
    engine = MagicMock()
    monkeypatch.setattr(c, "create_engine", lambda *_: engine)
    monkeypatch.setattr(c, "_fetch_referenced_editions", lambda *_: [("cannes", "2024")])
    source = c.MubiCncAirbyteSource()
    source._scrape_cnc_film_awards = AsyncMock(return_value=([], []))
    source._scrape_festival_editions = AsyncMock(return_value=[{"scrape_status": "blocked"}])
    with pytest.raises(RuntimeError, match="incomplète"):
        source.sync_to_postgres({"database_url": "sqlite://"})
    assert source._scrape_festival_editions.call_args.args[1] == [("cannes", "2024")]


def test_timeout_retry_reopens_browser_and_block_does_not_retry():
    source = c.MubiCncAirbyteSource()
    session = AsyncMock()
    session.fetch_html.side_effect = [TimeoutError(), "ok"]
    cfg = config(fetch_retry_base_delay_seconds=0)
    assert asyncio.run(source._fetch_with_retry(session, "url", cfg, "test")) == ("ok", None)
    session.__aexit__.assert_awaited_once()
    session.__aenter__.assert_awaited_once()
    session.reset_mock()
    session.fetch_html.side_effect = c.WebsiteBlockedError("429")
    _, error = asyncio.run(source._fetch_with_retry(session, "url", cfg, "test"))
    assert isinstance(error, c.WebsiteBlockedError)
    session.__aenter__.assert_not_awaited()


def test_checkpoint_deduplicates_batch_and_existing_snapshot(monkeypatch):
    engine = MagicMock()
    monkeypatch.setattr(c, "create_engine", lambda *_: engine)
    monkeypatch.setattr(c, "_fetch_existing_hashes", lambda *_: {"old"})
    insert = Mock()
    source = c.MubiCncAirbyteSource()
    source._insert_deduped(config(), "t", [{"record_hash": "old"}, {"record_hash": "new"}, {"record_hash": "new"}], insert)
    assert insert.call_args.args[2] == [{"record_hash": "new"}]


@pytest.mark.parametrize("failure", [None, "airbyte", "scrape", "dbt"])
def test_flow_publishes_only_after_successful_scraping(failure):
    calls = Mock()
    if failure:
        getattr(calls, failure).side_effect = RuntimeError(failure)
    with patch.object(flows.IngestionRequestSettings, "from_env", return_value="settings"), \
         patch.object(flows, "_mark_request_processing", calls.processing), \
         patch.object(flows, "_run_airbyte_sync_step", calls.airbyte), \
         patch.object(flows, "_run_mubi_cnc_scraping_step", calls.scrape), \
         patch.object(flows, "_run_dbt_phase_2_step", calls.dbt), \
         patch.object(flows, "_mark_request_failed", calls.failed), \
         patch.object(flows, "_mark_request_success", calls.success):
        kwargs = dict(request_id=str(uuid4()), visa_number="123", force_rescrape=True)
        if failure:
            with pytest.raises(RuntimeError):
                flows.run_mubi_cnc_scraping.fn(**kwargs)
        else:
            flows.run_mubi_cnc_scraping.fn(**kwargs)
    stages = ["processing", "airbyte", "scrape", "dbt", "success"]
    assert [x[0] for x in calls.mock_calls] == (stages if not failure else stages[:stages.index(failure) + 1] + ["failed"])


def test_mubi_dispatch_preserves_sync_and_target():
    settings = SimpleNamespace(airbyte_connection_names=["Sheets"])
    row = dict(request_id=uuid4(), request_type="mubi", max_films=1, visa_number="123", force_rescrape=True,
               request_source="metabase", requested_by_metabase_user="test")
    client = AsyncMock()
    client.read_deployment_by_name.return_value = SimpleNamespace(id=uuid4())
    client.create_flow_run_from_deployment.return_value = SimpleNamespace(id=uuid4())
    context = AsyncMock()
    context.__aenter__.return_value = client
    with patch.object(flows, "get_client", return_value=context):
        asyncio.run(flows._trigger_ingestion_request_run(settings, request_row=row))
    client.read_deployment_by_name.assert_awaited_once_with(flows.MUBI_CNC_DEPLOYMENT_NAME)
    params = client.create_flow_run_from_deployment.call_args.kwargs["parameters"]
    assert params["visa_number"] == "123" and params["force_rescrape"] is True
    assert params["airbyte_connection_names"] == ["Sheets"]


def test_cli_forcing_requires_target(monkeypatch):
    monkeypatch.setattr(cli, "_load_dotenv", Mock())
    monkeypatch.setattr("sys.argv", ["mubi", "sync", "--force"])
    with pytest.raises(SystemExit):
        cli.main()


def test_dashboard_actions_filters_and_counting():
    cards = dashboard.dashboard_cards()
    for targeted in (False, True):
        action = dashboard.action_body(1, 38, targeted=targeted)
        assert "'mubi'" in action["dataset_query"]["native"]["query"]
        assert "Airbyte" in action["description"] and "dbt" in action["description"]
    for card in cards:
        q = dashboard.publisher.dataset_query(1, card["query"], 99, parameters=dashboard.PARAMETERS)
        if "periode" in q["native"]["template-tags"]:
            assert q["native"]["template-tags"]["periode"]["dimension"] == ["field", 99, None]
    assert "DISTINCT run_id, mubi_id" in next(x["query"] for x in cards if x["display"] == "bar")


def test_postgres_resume_snapshot_and_shared_program(monkeypatch):
    """Tables temporaires uniquement ; activer explicitement pour vérifier PostgreSQL."""
    import os
    if os.environ.get("RIC_MUBI_TEST_DB") != "1":
        pytest.skip("RIC_MUBI_TEST_DB=1 autorise les tables temporaires")
    from sqlalchemy import create_engine
    cli._load_dotenv(cli.DEFAULT_ENV_PATH)
    raw = cli._load_json(str(ROOT / "ingestion/scraping/mubi_cnc/config.json"))
    engine = create_engine(c.ConnectorConfig.from_dict(raw).database_url, pool_size=1, max_overflow=0)
    try:
        with engine.begin() as db:
            db.execute(text('CREATE TEMP TABLE id_matching ("VISA" text, "ID_MUBI" text)'))
            schema = db.execute(text('SELECT nspname FROM pg_namespace WHERE oid=pg_my_temp_schema()')).scalar_one()
            cfg = c.ConnectorConfig.from_dict({**raw, "input_schema": schema, "output_schema": schema})
            c._ensure_film_awards_table(db, cfg)
            c._ensure_festival_films_table(db, cfg)
            db.execute(text(f'INSERT INTO "{schema}".id_matching VALUES (\'1\',\'123\'), (\'2\',\'123\'), (\'3\',NULL)'))
            assert c._fetch_pending_mubi_ids(db, cfg) == [123]
            r = c._award_record("r1", "2026-11-16T10:00:00Z", "/films/example", 123,
                festival="Cannes", year="2024", distinction=None, award="Sélection", scrape_status="success",
                error_message=None, event_slug="cannes", event_type="festival")
            c._insert_film_awards(db, cfg, [r])
            assert c._fetch_pending_mubi_ids(db, cfg) == []
            assert [tuple(x) for x in c._fetch_referenced_editions(db, cfg)] == [("cannes", "2024")]
            cfg.visa_number = "2"
            assert [tuple(x) for x in c._fetch_referenced_editions(db, cfg)] == [("cannes", "2024")]
            # Un nouveau succès sans palmarès remplace les éditions de l’ancien snapshot.
            r = c._award_record("r2", "2026-11-16T11:00:00Z", "/films/example", 123,
                festival=None, year=None, distinction=None, award=None, scrape_status="no_awards", error_message=None)
            c._insert_film_awards(db, cfg, [r])
            assert list(c._fetch_referenced_editions(db, cfg)) == []
            # Migration de file : contraintes, historique et verrou inter-sources.
            sql = (ROOT / "infra/data/ops-ingestion-table.sql").read_text()
            sql = sql.replace("SET ROLE dbt_user;", "").replace("RESET ROLE;", "").replace("ops.", f'"{schema}".')
            db.connection.driver_connection.execute(sql)
            db.execute(text(f"INSERT INTO \"{schema}\".ingestion_run_requests (requested_by_metabase_user,request_reason,request_type,max_films,visa_number,dedupe_key) VALUES ('test','test','mubi',1,'1','mubi')"))
            with db.begin_nested() as savepoint:
                with pytest.raises(Exception, match="global_active"):
                    db.execute(text(f"INSERT INTO \"{schema}\".ingestion_run_requests (requested_by_metabase_user,request_reason,request_type,max_films,dedupe_key) VALUES ('test','test','allocine',10,'allocine')"))
                savepoint.rollback()
    finally:
        engine.dispose()


def test_mubi_waits_for_payload_without_network_idle():
    from test_allocine_timeouts import session_with_page
    browser = session_with_page(navigation_wait_until="domcontentloaded", ready_selector="script#__NEXT_DATA__")
    browser.page.wait_for_selector = AsyncMock()
    asyncio.run(browser.fetch_html("https://mubi.com/fr/films/123/awards"))
    browser.page.wait_for_selector.assert_awaited_once_with("script#__NEXT_DATA__", state="attached", timeout=30000)
    browser.page.wait_for_load_state.assert_not_awaited()


def test_existing_table_requires_owner_migration(monkeypatch):
    monkeypatch.setattr(c, "_table_exists", lambda *_: True)
    db = Mock()
    db.execute.return_value = [("mubi_id",)]
    with pytest.raises(RuntimeError, match="Migration requise"):
        c._ensure_film_awards_table(db, config())
    assert all('ALTER TABLE' not in str(call.args[0]) for call in db.execute.call_args_list)


@pytest.mark.parametrize("body,expected", [("", "empty"),
    ('<a href="/films/example"><h3>Titre</h3></a>', "error"),
    ('<li class="css-l31k08"><a class="css-122y91a" href="/films/example"><h3>Titre</h3></a></li>', "success")])
def test_edition_empty_success_and_selector_drift(monkeypatch, body, expected):
    engine = MagicMock()
    monkeypatch.setattr(c, "create_engine", lambda *_: engine)
    monkeypatch.setattr(c, "_fetch_processed_page_combos", lambda *_: set())
    monkeypatch.setattr(c, "_fetch_edition_empty_boundaries", lambda *_: {})
    browser = AsyncMock()
    browser.__aenter__.return_value = browser
    monkeypatch.setattr("ingestion.scraping.browser.AsyncBrowserSession", Mock(return_value=browser))
    props = {"industryEvent": {"slug": "cannes"}, "yearsAvailable": [2024]}
    html = '<script id="__NEXT_DATA__">' + json.dumps({"props": {"pageProps": props}}) + '</script>' + body
    source = c.MubiCncAirbyteSource()
    source._checkpoint = Mock()
    source._fetch_with_retry = AsyncMock(return_value=(html, None))
    records = asyncio.run(source._scrape_festival_editions(config(max_pages_per_edition=1), [("cannes", "2024")]))
    assert records[0]["scrape_status"] == expected
    source._checkpoint.assert_called_once()


def test_dashboard_default_includes_current_day_without_changing_allocine():
    assert next(p for p in dashboard.PARAMETERS if p["id"] == "periode")["default"] == "past7days~"
    assert next(p for p in dashboard.publisher.PARAMETERS if p["id"] == "periode")["default"] == "past7days"
