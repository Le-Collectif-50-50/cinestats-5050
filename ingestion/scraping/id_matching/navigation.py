"""Session Playwright réutilisant les mécanismes du navigateur d'ingestion."""

import asyncio
import random
import sys
import time
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError

from ingestion.scraping.browser import (
    BLOCKED_PAGE_MARKERS,
    AsyncBrowserSession,
    WebsiteBlockedError,
)


class MissingPage(RuntimeError):
    pass


class Browser(AsyncBrowserSession):
    """Pauses globales, reprises bornées et arrêt par domaine en cas de blocage."""

    def __init__(self, *, delay_min=3, delay_max=6, timeout=35, attempts=2, **kwargs):
        super().__init__(stealth=False, solve=False, **kwargs)
        self.delay_min, self.delay_max = delay_min, delay_max
        self.timeout, self.attempts = timeout, attempts
        self.last_request = 0
        self.blocked = {}

    async def pause(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(max(0, delay - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()

    async def consent(self):
        """Consentements MUBI/CookieYes et TMDB/OneTrust."""
        selectors = [
            "button.cky-btn-accept",
            "#onetrust-accept-btn-handler",
        ]
        for frame in self.page.frames:
            for selector in selectors:
                button = frame.locator(selector).first
                try:
                    if await button.is_visible():
                        await button.click(timeout=2000)
                        await self.page.wait_for_timeout(400)
                except PlaywrightError:
                    continue

    async def checked_html(self, response=None):
        status = response.status if response else 200
        host = urlparse(self.page.url).hostname
        text = (await self.page.locator("body").inner_text(timeout=5000)).lower()
        markers = [
            *BLOCKED_PAGE_MARKERS,
            "your access is temporarily blocked",
            "vérifiez que vous êtes humain",
            "unusual traffic from your computer",
        ]
        if status in (403, 429) or any(m in text for m in markers):
            reason = f"Accès bloqué sur {host} (HTTP {status}). Domaine suspendu pour cette exécution."
            self.blocked[host] = reason
            raise WebsiteBlockedError(reason)
        if status in (404, 410):
            raise MissingPage(f"Fiche inexistante (HTTP {status}) : {self.page.url}")
        if status >= 400:
            raise RuntimeError(f"Erreur HTTP {status} : {self.page.url}")
        return await self.page.content()

    async def settle(self, response=None):
        await self.page.wait_for_timeout(1200)
        await self.consent()
        await self.page.mouse.wheel(0, random.uniform(300, 700))
        await self.page.wait_for_timeout(600)
        await self.consent()
        return await self.checked_html(response)

    async def fetch_html(self, url):
        host = urlparse(url).hostname
        if host in self.blocked:
            raise WebsiteBlockedError(self.blocked[host])
        for attempt in range(self.attempts):
            await self.pause()
            try:
                response = await self.page.goto(
                    url, wait_until="domcontentloaded", timeout=self.timeout * 1000
                )
                html = await self.settle(response)
                if host == "mubi.com" and "/search" in urlparse(url).path:
                    switch = self.page.locator("#switch-button-search-page")
                    await switch.wait_for(state="attached", timeout=10000)
                    if not await switch.is_checked():
                        await self.pause()
                        await self.page.locator('label[for="switch-button-search-page"]').click(
                            timeout=5000
                        )
                    await self.page.wait_for_timeout(2000)
                    if not await switch.is_checked():
                        raise RuntimeError("MUBI : filtre Tous les films non activé.")
                    html = await self.checked_html()
                return html
            except (WebsiteBlockedError, MissingPage):
                raise
            except (PlaywrightError, RuntimeError) as exc:
                if attempt + 1 == self.attempts:
                    raise
                print(f"Nouvelle tentative : {type(exc).__name__}", file=sys.stderr, flush=True)
                await asyncio.sleep(min(30, 3 * 2**attempt))
                if not self.browser.is_connected():
                    await self.__aexit__(None, None, None)
                    await self.__aenter__()
                elif self.page.is_closed():
                    self.page = await self.context.new_page()
        raise RuntimeError("Aucune tentative exécutée.")
