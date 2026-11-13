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
        url="about:blank",
        close=AsyncMock(),
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
        assert session.lightweight is True
        assert session.navigation_timeout_seconds == 60
        assert session.navigation_wait_until == "domcontentloaded"
        manager.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("url,kind,blocked", [
    ("https://www.allocine.fr/film/1", "document", False),
    ("https://assets.allocine.fr/app.js", "script", False),
    ("https://www.google.com/recaptcha/api.js", "script", False),
    ("https://challenges.cloudflare.com/turnstile/", "document", False),
    ("https://images.example.org/poster.jpg", "image", True),
    ("https://video.example.org/trailer.mp4", "media", True),
    ("https://static.example.org/font.woff", "font", True),
    ("https://sync.drift-pixel.ai/sync", "document", True),
    ("https://ap.lijit.com/sync", "document", True),
    ("https://www.allocine.fr/?next=lijit.com", "document", False),
])
def test_lightweight_routes_keep_content_and_access_controls(url, kind, blocked):
    route = SimpleNamespace(abort=AsyncMock(), continue_=AsyncMock())
    request = SimpleNamespace(url=url, resource_type=kind)
    asyncio.run(AsyncBrowserSession(lightweight=True)._route_request(route, request))
    assert route.abort.await_count == int(blocked)
    assert route.continue_.await_count == int(not blocked)


def test_default_routes_keep_images():
    route = SimpleNamespace(abort=AsyncMock(), continue_=AsyncMock())
    request = SimpleNamespace(url="https://mubi.com/poster.jpg", resource_type="image")
    asyncio.run(AsyncBrowserSession()._route_request(route, request))
    route.continue_.assert_awaited_once()


def test_lightweight_closes_previous_page_before_navigation():
    session = session_with_page(lightweight=True)
    old_page = SimpleNamespace(url="https://www.allocine.fr/film/1", close=AsyncMock())
    new_page = session.page
    session.page = old_page
    session.context = SimpleNamespace(new_page=AsyncMock(return_value=new_page))
    asyncio.run(session.fetch_html("https://www.allocine.fr/film/1/casting/"))
    old_page.close.assert_awaited_once()
    new_page.goto.assert_awaited_once()


def test_cleanup_continues_after_hung_page(monkeypatch):
    monkeypatch.setattr("ingestion.scraping.browser.BROWSER_CLOSE_TIMEOUT_SECONDS", 0.01)
    session = session_with_page()

    async def hang():
        await asyncio.Event().wait()

    session.page.close = hang
    session.context = SimpleNamespace(close=AsyncMock())
    session.browser = SimpleNamespace(close=AsyncMock())
    session.playwright = SimpleNamespace(stop=AsyncMock())
    asyncio.run(session.__aexit__(None, None, None))
    session.context.close.assert_awaited_once()
    session.browser.close.assert_awaited_once()
    session.playwright.stop.assert_awaited_once()


def test_hung_previous_page_is_replaced_before_fetch(monkeypatch):
    monkeypatch.setattr("ingestion.scraping.browser.BROWSER_CLOSE_TIMEOUT_SECONDS", 0.01)
    session = session_with_page(lightweight=True)
    fresh_page = session.page

    async def hang():
        await asyncio.Event().wait()

    async def reopen():
        session.page = fresh_page
        return session

    session.page = SimpleNamespace(url="https://www.allocine.fr/film/1", close=hang)
    session.__aexit__ = AsyncMock()
    session.__aenter__ = AsyncMock(side_effect=reopen)
    assert "Film" in asyncio.run(session.fetch_html("https://www.allocine.fr/film/1/casting/"))
    session.__aexit__.assert_awaited_once()
    session.__aenter__.assert_awaited_once()
    fresh_page.goto.assert_awaited_once()


def test_session_replacement_has_finite_budget(monkeypatch):
    monkeypatch.setattr("ingestion.scraping.browser.BROWSER_CLOSE_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr("ingestion.scraping.browser.BROWSER_OPEN_TIMEOUT_SECONDS", 0.01)
    session = session_with_page(lightweight=True)

    async def hang():
        await asyncio.Event().wait()

    session.page.url = "https://www.allocine.fr/film/1"
    session.page.close = hang
    session.__aexit__ = AsyncMock()
    session.__aenter__ = hang
    with pytest.raises(RuntimeError, match="session replacement timed out"):
        asyncio.run(session.fetch_html("https://www.allocine.fr/film/1/casting/"))
    session.page.content.assert_not_awaited()


@pytest.mark.parametrize("status,expected_sessions", [("success", 2), ("blocked", 2)])
def test_each_film_gets_own_session_without_retrying_blocked(status, expected_sessions):
    managers = []

    def factory(**kwargs):
        manager = SimpleNamespace(__aenter__=AsyncMock(), __aexit__=AsyncMock())
        managers.append(manager)
        return manager

    source = AllocineAirbyteSource()
    source._scrape_one_record = AsyncMock(return_value={"scrape_status": status})
    asyncio.run(source._scrape_chunk("test", [{"allocine_id": 1}, {"allocine_id": 2}],
        factory, None, config(inter_film_delay_min_seconds=0, inter_film_delay_max_seconds=0)))
    assert len(managers) == expected_sessions
    for manager in managers:
        manager.__aexit__.assert_awaited_once()


def test_failed_session_open_is_closed_and_retried():
    managers = []

    def factory(**kwargs):
        manager = SimpleNamespace(__aenter__=AsyncMock(side_effect=RuntimeError("CDP timeout")),
                                  __aexit__=AsyncMock())
        managers.append(manager)
        return manager

    rows = asyncio.run(AllocineAirbyteSource()._scrape_chunk(
        "test", [{"allocine_id": 1}], factory, None, config()))
    assert rows[0]["scrape_status"] == "error"
    assert len(managers) == 2
    for manager in managers:
        manager.__aexit__.assert_awaited_once()


def test_session_open_timeout_is_bounded_and_distinct_from_record_timeout(monkeypatch):
    monkeypatch.setattr("ingestion.scraping.allocine.connector.SESSION_OPEN_TIMEOUT_SECONDS", 0.01)
    managers = []

    async def hang():
        await asyncio.Event().wait()

    def factory(**kwargs):
        manager = SimpleNamespace(__aenter__=hang, __aexit__=AsyncMock())
        managers.append(manager)
        return manager

    rows = asyncio.run(AllocineAirbyteSource()._scrape_chunk(
        "test", [{"allocine_id": 1}], factory, None, config()))
    assert rows[0]["scrape_status"] == "error"
    assert "session opening timed out" in rows[0]["error_message"]
    assert len(managers) == 2
    for manager in managers:
        manager.__aexit__.assert_awaited_once()
