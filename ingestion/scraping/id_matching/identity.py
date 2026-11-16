"""Identité MUBI/TMDB, adaptée du matcher local de visas."""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ingestion.scraping.mubi.mubi_scraper import MubiPageScraper


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def title_norm(value):
    value = str(value)
    article = re.search(r"\s*\((le|la|les|l['’]|un|une|des|the)\)$", value, re.I)
    if article:
        value = article.group(1) + " " + value[: article.start()]
    return norm(value)


def number(value):
    if value is None or isinstance(value, bool):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+(?:\.0+)?", text):
        integer = int(text.split(".", 1)[0])
        return str(integer) if integer > 0 else ""
    return ""


@dataclass
class Film:
    provider: str
    id: str = ""
    title: str = ""
    directors: list[str] = field(default_factory=list)
    year: str = ""
    visa: str = ""
    url: str = ""
    aliases: list[str] = field(default_factory=list)
    visa_date: str = ""


def soup_of(html):
    return BeautifulSoup(html, "html.parser")


def labelled(soup, label):
    """TMDB place le titre original en texte dans le même paragraphe que son libellé."""
    for paragraph in soup.select("section.facts p, section.header p"):
        heading = paragraph.find("strong")
        if heading and norm(heading.get_text(" ", strip=True)) == norm(label):
            value = paragraph.get_text(" ", strip=True)
            prefix = heading.get_text(" ", strip=True)
            return value[len(prefix) :].strip()
    return ""


def movie_ld(soup):
    def walk(obj):
        if isinstance(obj, list):
            for item in obj:
                yield from walk(item)
        elif isinstance(obj, dict):
            types = obj.get("@type", [])
            types = [types] if isinstance(types, str) else types
            if "Movie" in types:
                yield obj
            yield from walk(obj.get("@graph", []))

    for script in soup.select('script[type="application/ld+json"]'):
        try:
            yield from walk(json.loads(script.get_text()))
        except (ValueError, TypeError):
            continue


def people(value):
    if not value:
        return []
    if isinstance(value, (str, dict)):
        value = [value]
    return [x.get("name", "") if isinstance(x, dict) else str(x) for x in value]


def provider_id(provider, url):
    path = urlparse(url).path
    if provider == "tmdb":
        match = re.fullmatch(r"/movie/(\d+)(?:-[^/]*)?/?", path)
    else:
        match = re.search(r"/films/([^/]+)/?$", path)
    return match.group(1) if match else ""


def parse_film(provider, html, url):
    soup = soup_of(html)
    ld = next(movie_ld(soup), {})
    film = Film(provider, provider_id(provider, url), url=url)
    film.title = str(ld.get("name") or "")
    film.directors = people(ld.get("director"))
    film.year = str(ld.get("datePublished") or "")[:4]
    if provider == "mubi":
        scraper = MubiPageScraper()
        props = scraper._next_page_props(html)
        data = props.get("film") or props.get("initFilm") or {}
        film.id = number(scraper.extract_film_mubi_id(html)) or number(data.get("id"))
        film.title = data.get("title") or film.title
        film.directors = people(data.get("directors")) or film.directors
        film.year = str(data.get("year") or film.year)
        film.aliases = [
            str(data[k]) for k in ("original_title", "originalTitle") if data.get(k)
        ]
    else:
        title = soup.select_one("section.header .title h2 a")
        if title:
            film.title = title.get_text(" ", strip=True)
        year = soup.select_one("section.header .title .release_date")
        if year:
            film.year = year.get_text(strip=True).strip("()")
        for node in soup.select("section.header ol.people li.profile"):
            job = node.select_one(".character")
            if job and re.search(r"director|réalisat", job.get_text(), re.I):
                name = node.select_one("a")
                if name:
                    film.directors.append(name.get_text(" ", strip=True))
        original = labelled(soup, "Titre d'origine") or labelled(soup, "Original Title")
        if original:
            film.aliases.append(original)
    film.directors = list(dict.fromkeys(film.directors))
    if not film.title or not film.id:
        raise ValueError(f"Fiche {provider} sans titre ou identifiant exploitable.")
    return film


def assess(reference, candidate):
    """Un titre seul ne valide jamais une identité. Pas de score assimilé à une probabilité."""
    titles = [reference.title, *reference.aliases]
    other_titles = [candidate.title, *candidate.aliases]
    title_ok = bool(
        {title_norm(x) for x in titles if title_norm(x)}
        & {title_norm(x) for x in other_titles if title_norm(x)}
    )
    ref_names = {tuple(sorted(norm(x).split())) for x in reference.directors if norm(x)}
    other_names = {tuple(sorted(norm(x).split())) for x in candidate.directors if norm(x)}
    director_ok = bool(ref_names & other_names)
    if title_ok and director_ok:
        return "confirme", "Titre et réalisateur concordent avec le CNC."
    if ref_names and other_names and not director_ok:
        return "incompatible", "Réalisateur différent de la fiche CNC."
    return (
        "a_revoir",
        "Preuves insuffisantes : titre et réalisateur concordants requis.",
    )


def search_links(provider, html, url, title):
    soup = soup_of(html)
    if provider == "mubi" and any(
        marker in soup.get_text(" ", strip=True).lower()
        for marker in ("nous n’avons pas trouvé", "we couldn't find", "no results")
    ):
        # Les cartes sous ce message sont des recommandations, pas des résultats.
        return []
    selector = {
        "mubi": 'a[href*="/films/"]',
        "tmdb": '.search_results a[href*="/movie/"], .results a[href*="/movie/"]',
    }[provider]
    links = {}
    for a in soup.select(selector):
        target = urljoin(url, a.get("href", ""))
        if urlparse(target).hostname != urlparse(url).hostname:
            continue
        key = provider_id(provider, target)
        if key:
            name = a.get_text(" ", strip=True) or a.get("title", "")
            similarity = SequenceMatcher(None, title_norm(title), title_norm(name)).ratio()
            if key not in links or similarity > links[key][0]:
                links[key] = (similarity, target)
    return [url for _, url in sorted(links.values(), reverse=True)]
