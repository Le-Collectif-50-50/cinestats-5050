"""Recherche de candidats, puis vérification indépendante de leur identité."""

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
from urllib.parse import quote_plus

from ingestion.scraping.browser import WebsiteBlockedError

from .identity import assess, parse_film, search_links, soup_of

SEARCH = {
    "mubi": "https://mubi.com/fr/search/films?query={}&page=1&all_films=true",
    "tmdb": "https://www.themoviedb.org/search/movie?query={}&language=fr-FR",
}
EMPTY_MARKERS = (
    "aucun résultat",
    "aucun film",
    "pas de résultat",
    "no results",
    "no movies",
    "0 résultat",
    "nothing found",
    "aucun élément",
    "nous n’avons pas trouvé",
    "we couldn't find",
)


async def match(browser, reference, provider, *, max_candidates=10, timeout=180):
    result = {
        "visa": reference.visa,
        "provider": provider,
        "status": "a_revoir",
        "confirmed_id": "",
        "reference": asdict(reference),
        "candidates": [],
        "reason": "",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    if not reference.title or not reference.directors:
        result["reason"] = "Titre ou réalisateur CNC absent/ambigu : validation impossible."
        return result
    try:
        async with asyncio.timeout(timeout):
            url = SEARCH[provider].format(quote_plus(reference.title))
            html = await browser.fetch_html(url)
            links = search_links(provider, html, browser.page.url, reference.title)
            if not links:
                text = soup_of(html).get_text(" ", strip=True).lower()
                if not any(marker in text for marker in EMPTY_MARKERS):
                    raise ValueError("Recherche non reconnue : vérifier sélecteurs/chargement.")
            incomplete = len(links) > max_candidates
            errors = []
            confirmed = {}
            for link in links[:max_candidates]:
                try:
                    html = await browser.fetch_html(link)
                    candidate = parse_film(provider, html, browser.page.url)
                    state, reason = assess(reference, candidate)
                    result["candidates"].append(
                        {
                            **asdict(candidate),
                            "assessment": state,
                            "reason": reason,
                        }
                    )
                    if state == "confirme":
                        confirmed[candidate.id] = candidate
                except WebsiteBlockedError:
                    raise
                except Exception as exc:
                    incomplete = True
                    errors.append(f"Candidat illisible : {link} ({type(exc).__name__}).")
            if len(confirmed) > 1:
                result.update(status="ambigu", reason="Plusieurs fiches concordantes.")
            elif len(confirmed) == 1 and not incomplete:
                result.update(
                    status="trouve",
                    confirmed_id=next(iter(confirmed)),
                    reason="Titre et réalisateur concordants sur fiche détaillée.",
                )
            elif incomplete or any(c["assessment"] == "a_revoir" for c in result["candidates"]):
                result["reason"] = (
                    "Contrôle incomplet, limite atteinte ou identité insuffisante."
                )
            else:
                result.update(
                    status="non_trouve", reason="Aucun candidat confirmé dans cette recherche."
                )
            if errors:
                result["reason"] += " " + " ".join(errors)
    except WebsiteBlockedError:
        result.update(
            status="bloque", confirmed_id="", reason="Accès bloqué ; domaine suspendu."
        )
    except Exception as exc:
        result.update(
            status="erreur", confirmed_id="", reason=f"Échec recherche ({type(exc).__name__})."
        )
    return result
