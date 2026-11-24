"""Bornes, reprise et orchestration Mubi, sans réseau ni données persistées."""

import asyncio
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from ingestion.prefect import flows
from ingestion.scraping.mubi_cnc import bounded as b, connector as c, main as cli


def config(**kwargs):
    return c.ConnectorConfig.from_dict({"database_url": "sqlite://", **kwargs})


def test_page_selection_resumes_and_obeys_empty_boundary(monkeypatch):
    monkeypatch.setattr(c, "_fetch_processed_page_combos", lambda *_: {("cannes", 2024, 1)})
    monkeypatch.setattr(c, "_fetch_edition_empty_boundaries", lambda *_: {("cannes", 2024): 4})
    assert c._pending_edition_pages(
        None, config(max_pages_per_edition=100), [("cannes", "2024"), ("cannes", "2024")]
    ) == [("cannes", 2024, 2), ("cannes", 2024, 3)]


def test_budget_preserves_completed_checkpoints():
    checkpoints = []

    async def collect(_):
        checkpoints.append("completed-first-film")
        await asyncio.sleep(1)
        checkpoints.append("unfinished-second-film")

    source = SimpleNamespace(_scrape_cnc_film_awards=collect)
    assert asyncio.run(b.collect_phase(source, config(), "awards", 25, 0.02)) is True
    assert checkpoints == ["completed-first-film"]


def test_non_budget_timeouts_are_failures():
    source = SimpleNamespace(
        _scrape_cnc_film_awards=AsyncMock(side_effect=TimeoutError("connection"))
    )
    with pytest.raises(TimeoutError, match="connection"):
        asyncio.run(b.collect_phase(source, config(), "awards", 25, 10))


def test_bounded_phase_errors_prevent_success(monkeypatch):
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.execute.return_value.all.return_value = [
        ("blocked", 1)
    ]
    monkeypatch.setattr(b, "create_engine", lambda *_: engine)
    for name in ("_ensure_schema", "_ensure_film_awards_table", "_ensure_festival_films_table"):
        monkeypatch.setattr(b, name, Mock())
    monkeypatch.setattr(b, "collect_phase", AsyncMock(return_value=False))
    with pytest.raises(RuntimeError, match="incomplète"):
        b.run_phase({"database_url": "sqlite://"}, phase="awards")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"job_timeout_seconds": 901},
        {"job_timeout_seconds": True},
        {"page_limit": 0},
        {"phase": "all"},
    ],
)
def test_invalid_bounds_rejected(kwargs):
    with pytest.raises(ValueError):
        b.run_phase({"database_url": "sqlite://"}, **{"phase": "awards", **kwargs})


def test_orchestrator_runs_batches_sequentially_and_resumes_festivals(monkeypatch):
    state = {"film_ids": list(range(1, 24)), "festival_pages": 53}
    calls = []
    monkeypatch.setattr(flows, "get_run_logger", Mock())
    monkeypatch.setattr(
        flows,
        "_mubi_pending",
        lambda *_: {
            "film_ids": list(state["film_ids"]),
            "festival_pages": state["festival_pages"],
        },
    )

    def awards(**kwargs):
        calls.append(("awards", kwargs["max_films"]))
        del state["film_ids"][: kwargs["max_films"]]

    def festivals(**kwargs):
        calls.append(("festivals", kwargs["page_limit"]))
        state["festival_pages"] = max(0, state["festival_pages"] - kwargs["page_limit"])

    monkeypatch.setattr(flows, "run_mubi_awards_batch", awards)
    monkeypatch.setattr(flows, "run_mubi_festival_batch", festivals)
    flows._run_mubi_cnc_scraping_step(max_films=23)
    assert calls == [
        ("awards", 10),
        ("awards", 10),
        ("awards", 3),
        ("festivals", 25),
        ("festivals", 25),
        ("festivals", 25),
    ]
    calls.clear()
    flows._run_mubi_cnc_scraping_step(max_films=23)
    assert calls == []


def test_no_progress_stops_pipeline(monkeypatch):
    monkeypatch.setattr(flows, "get_run_logger", Mock())
    monkeypatch.setattr(
        flows, "_mubi_pending", lambda *_: {"film_ids": [1], "festival_pages": 0}
    )
    monkeypatch.setattr(flows, "run_mubi_awards_batch", Mock())
    with pytest.raises(RuntimeError, match="sans progression"):
        flows._run_mubi_cnc_scraping_step()


def test_festival_phase_has_page_and_process_limits(monkeypatch):
    run = Mock()
    monkeypatch.setattr(flows, "_run", run)
    flows.run_mubi_festival_batch.fn(
        config_path="config", page_limit=25, job_timeout_seconds=600
    )
    command = run.call_args.args[0]
    assert command[command.index("--phase") + 1] == "festivals"
    assert command[command.index("--page-limit") + 1] == "25"
    assert run.call_args.kwargs["timeout_seconds"] == 660


def test_process_watchdog_terminates_real_child(monkeypatch):
    monkeypatch.setattr(flows, "get_run_logger", Mock())
    start = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        flows._run(
            [sys.executable, "-c", "import time;time.sleep(60)"], "test", timeout_seconds=0.2
        )
    assert time.monotonic() - start < 5


def test_cli_selects_only_requested_phase(monkeypatch):
    monkeypatch.setattr(cli, "_load_dotenv", Mock())
    monkeypatch.setattr(cli, "_load_json", lambda *_: {})
    run = Mock()
    monkeypatch.setattr(b, "run_phase", run)
    monkeypatch.setattr(
        sys, "argv", ["mubi", "sync", "--phase", "festivals", "--page-limit", "3"]
    )
    assert cli.main() == 0
    assert run.call_args.kwargs["phase"] == "festivals"
    assert run.call_args.kwargs["page_limit"] == 3


def test_festival_collection_requests_no_more_than_page_limit(monkeypatch):
    import json

    engine = MagicMock()
    monkeypatch.setattr(c, "create_engine", lambda *_: engine)
    monkeypatch.setattr(c, "_fetch_processed_page_combos", lambda *_: set())
    monkeypatch.setattr(c, "_fetch_edition_empty_boundaries", lambda *_: {})
    browser = AsyncMock()
    browser.__aenter__.return_value = browser
    monkeypatch.setattr(
        "ingestion.scraping.browser.AsyncBrowserSession", Mock(return_value=browser)
    )
    html = (
        '<script id="__NEXT_DATA__">'
        + json.dumps(
            {
                "props": {
                    "pageProps": {"industryEvent": {"slug": "cannes"}, "yearsAvailable": [2024]}
                }
            }
        )
        + "</script>"
    )
    html += '<li class="css-l31k08"><a class="css-122y91a" href="/films/example"><h3>Titre</h3></a></li>'
    source = c.MubiCncAirbyteSource()
    source._fetch_with_retry = AsyncMock(return_value=(html, None))
    source._checkpoint = Mock()
    cfg = config(
        max_pages_per_edition=100,
        inter_request_delay_min_seconds=0,
        inter_request_delay_max_seconds=0,
    )
    asyncio.run(source._scrape_festival_editions(cfg, [("cannes", "2024")], page_limit=2))
    assert source._fetch_with_retry.await_count == 2
    assert source._checkpoint.call_count == 2


@pytest.mark.parametrize(
    "kwargs", [{"batch_size": 0}, {"festival_page_limit": True}, {"job_timeout_seconds": 901}]
)
def test_invalid_job_bounds_never_start_airbyte(monkeypatch, kwargs):
    airbyte = Mock()
    monkeypatch.setattr(flows, "_run_airbyte_sync_step", airbyte)
    with pytest.raises(ValueError):
        flows.run_mubi_cnc_scraping.fn(**kwargs)
    airbyte.assert_not_called()
