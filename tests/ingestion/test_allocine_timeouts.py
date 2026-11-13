import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from ingestion.scraping.allocine.connector import AllocineAirbyteSource, ConnectorConfig
from ingestion.scraping.browser import AsyncBrowserSession, WebsiteBlockedError


def config(**overrides):
    return ConnectorConfig.from_dict({"database_url": "sqlite://", **overrides})


def session_with_page(**kwargs):
    session = AsyncBrowserSession(**kwargs)
    session.page = SimpleNamespace(
        goto=AsyncMock(return_value=SimpleNamespace(status=200)),
        wait_for_load_state=AsyncMock(),
        wait_for_timeout=AsyncMock(),
        mouse=SimpleNamespace(wheel=AsyncMock()),
        content=AsyncMock(return_value="<html><body>Film</body></html>"),
        locator=lambda _: SimpleNamespace(inner_text=AsyncMock(return_value="Film")),
    )
    session._dismiss_allocine_fullscreen_if_present = AsyncMock()
    session._accept_mubi_cookies_if_present = AsyncMock()
    return session


def test_allocine_reads_dom_without_waiting_for_network_idle():
    session = session_with_page(
        navigation_timeout_seconds=75, navigation_wait_until="domcontentloaded"
    )
    session.page.wait_for_load_state.side_effect = AssertionError("Network stays busy")
    assert "Film" in asyncio.run(session.fetch_html("https://www.allocine.fr/film/1"))
    session.page.goto.assert_awaited_once_with(
        "https://www.allocine.fr/film/1", wait_until="domcontentloaded", timeout=75000
    )
    session.page.wait_for_load_state.assert_not_awaited()


def test_other_scrapers_keep_navigation_defaults():
    session = session_with_page()
    asyncio.run(session.fetch_html("https://mubi.com/films/example"))
    assert session.page.goto.await_args.kwargs == {
        "wait_until": "networkidle",
        "timeout": 30000,
    }


@pytest.mark.parametrize("status", [403, 429])
def test_blocked_response_never_returns_html(status):
    session = session_with_page(navigation_wait_until="domcontentloaded")
    session.page.goto.return_value.status = status
    with pytest.raises(WebsiteBlockedError, match=str(status)):
        asyncio.run(session.fetch_html("https://www.allocine.fr/film/1"))
    session.page.content.assert_not_awaited()


def test_navigation_timeout_has_actionable_message():
    session = session_with_page(
        navigation_timeout_seconds=60, navigation_wait_until="domcontentloaded"
    )
    session.page.goto.side_effect = PlaywrightTimeoutError("Timeout 60000ms exceeded")
    with pytest.raises(RuntimeError, match="Navigation timed out after 60s"):
        asyncio.run(session.fetch_html("https://www.allocine.fr/film/1"))
    session.page.content.assert_not_awaited()


@pytest.mark.parametrize("value", [0, -1, "bad", float("inf"), float("nan")])
def test_navigation_timeout_requires_positive_finite_value(value):
    with pytest.raises(ValueError, match="navigation_timeout_seconds"):
        config(navigation_timeout_seconds=value)


def test_timeout_defaults_and_override():
    assert config().navigation_timeout_seconds == 60
    assert config().record_timeout_seconds == 240
    assert config(navigation_timeout_seconds="90").navigation_timeout_seconds == 90


@pytest.mark.parametrize("recovers", [True, False])
def test_navigation_timeout_reopens_browser_and_bounds_retries(recovers):
    sessions = []

    def factory(**kwargs):
        session = session_with_page(**kwargs)
        if not sessions or not recovers:
            session.page.goto.side_effect = PlaywrightTimeoutError("Timeout 60000ms exceeded")
        manager = SimpleNamespace(
            __aenter__=AsyncMock(return_value=session), __aexit__=AsyncMock()
        )
        sessions.append((session, manager))
        return manager

    source = AllocineAirbyteSource()

    async def scrape(**kwargs):
        try:
            await kwargs["session"].fetch_html("https://www.allocine.fr/film/1")
            return {"scrape_status": "success"}
        except Exception as exc:
            return {"scrape_status": "error", "error_message": str(exc)}

    source._scrape_one_record = scrape
    records = asyncio.run(
        source._scrape_chunk(
            "test", [{"source_record_id": "1", "allocine_id": 1}], factory, None, config()
        )
    )
    assert records[0]["scrape_status"] == ("success" if recovers else "error")
    assert len(sessions) == 2
    for session, manager in sessions:
        assert session.navigation_timeout_seconds == 60
        assert session.navigation_wait_until == "domcontentloaded"
        manager.__aexit__.assert_awaited_once()
