#!/usr/bin/env python3
"""Publier le dashboard Mubi CNC et ses actions, sans lancer de collecte."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("scraping_dashboard_publisher", Path(__file__).with_name("metabase-scraping-review.py"))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

NAME = "Scraping Mubi — Suivi CNC"
DESCRIPTION = (
    "Suivi Mubi piloté par le référentiel CNC. Couverture par visa ; état par ID Mubi distinct. "
    "Films, pages de festivals et lignes de palmarès sont des unités distinctes. "
    "Les boutons synchronisent Airbyte, collectent Mubi puis publient dbt. "
    "Aucun calendrier automatique. Les filtres ne ciblent pas les formulaires. "
    "Un ID partagé peut apparaître sur plusieurs visas sans constituer plusieurs événements. "
    "Les lignes de palmarès ne sont pas un décompte de prix remportés (voir issue 82)."
)
RAW_TABLE = "mubi_film_awards"
STATE_FILE = ROOT / "ingestion/scraping/mubi_cnc/local-runs/metabase-review-state.json"
PARAMETERS = [
    {**p, **({"default": "past7days~"} if p["id"] == "periode" else {})}
    for p in publisher.PARAMETERS
] + [
    {"id": "mubi", "name": "ID Mubi", "slug": "mubi", "type": "string/=", "sectionId": "string"},
]
BASE = """WITH films AS (
 SELECT * FROM ops.v_mubi_pipeline_status WHERE TRUE
 [[AND cnc_visa = {{visa}}]]
 [[AND title ILIKE '%' || {{titre}} || '%']]
 [[AND mubi_id = {{mubi}}]]
)
"""


def dashboard_cards():
    cards = []
    for i, (name, query) in enumerate([
        ("Visas sans ID Mubi", "SELECT count(*) AS visas FROM films WHERE eligibility = 'missing_id'"),
        ("ID Mubi en attente", "SELECT count(DISTINCT mubi_id) AS films FROM films WHERE eligibility = 'pending'"),
        ("ID Mubi traités", "SELECT count(DISTINCT mubi_id) AS films FROM films WHERE eligibility = 'completed'"),
        ("Derniers essais en erreur/blocage", "SELECT count(DISTINCT mubi_id) AS films FROM films WHERE scrape_status IN ('error', 'blocked')"),
    ]):
        cards.append(dict(name=name, query=BASE + query, display="scalar", col=i * 6, row=3, size_x=6, size_y=3))
    for i, (name, query) in enumerate([
        ("Films sans palmarès au dernier essai", "SELECT count(DISTINCT mubi_id) AS films FROM films WHERE scrape_status = 'no_awards'"),
        ("Visas avec ID Mubi invalide", "SELECT count(*) AS visas FROM films WHERE eligibility = 'invalid_id'"),
    ]):
        cards.append(dict(name=name, query=BASE + query, display="scalar", col=i * 12, row=6, size_x=12, size_y=3))
    cards.append(dict(name="Tentatives de films par heure", display="bar", col=0, row=9, size_x=24, size_y=8,
        query="""WITH attempts AS (
 SELECT DISTINCT run_id, mubi_id, extracted_at, scrape_status
 FROM raw.mubi_film_awards WHERE mubi_id IS NOT NULL [[AND {{periode}}]]
)
SELECT date_trunc('hour', extracted_at AT TIME ZONE 'Europe/Paris') AS heure,
 scrape_status AS statut, count(*) AS tentatives FROM attempts
GROUP BY 1, 2 ORDER BY 1, 2""",
        description="Une tentative par run, ID Mubi et horodatage ; les lignes de palmarès ne multiplient pas les tentatives. Période par défaut : sept jours précédents et aujourd’hui ; hors filtres visa, titre et ID Mubi.",
        visualization_settings={"graph.dimensions": ["heure", "statut"], "graph.metrics": ["tentatives"], "stackable.stack_type": "stacked"}))
    requests = (ROOT / "ingestion/dbt/analyses/metabase/scraping_requests.sql").read_text().replace("request_type = 'allocine'", "request_type = 'mubi'")
    # L’état et les erreurs restent visibles avant les champs longs du formulaire.
    requests = """SELECT etat_demande, demande_le, films_maximum, visa_cnc, erreur,
        demandeur, motif, terminee_le, execution_prefect, demande_id, retraitement_force
        FROM (""" + requests.rstrip().rstrip(";") + """ ) demandes
        ORDER BY demande_le DESC, demande_id DESC"""
    cards.append(dict(name="Demandes Mubi", query=requests, display="table", col=0, row=17, size_x=24, size_y=7,
        description="50 dernières demandes, hors filtres. Terminée : collecte sans erreur technique puis dbt réussi. Aucun film éligible peut produire une publication sans nouvelle collecte. Les annulations/crashes sont réconciliés par le poller."))
    cards.append(dict(name="État des films CNC", query=BASE + """SELECT cnc_visa AS visa, title AS titre, mubi_id,
 eligibility AS eligibilite, scrape_status AS dernier_statut,
 extracted_at AT TIME ZONE 'Europe/Paris' AS dernier_essai,
 last_success_at AT TIME ZONE 'Europe/Paris' AS dernier_succes,
 error_message AS motif, CASE WHEN film_link IS NOT NULL THEN 'https://mubi.com' || film_link END AS lien_mubi, run_id
FROM films ORDER BY extracted_at DESC NULLS FIRST, cnc_visa""", display="table", col=0, row=24, size_x=24, size_y=10))
    cards.append(dict(name="Éditions et pages de festivals", query="""WITH pages AS (
 SELECT DISTINCT ON (festival_slug, year, page_num) festival_slug, year, page_num,
 scrape_status, error_message, extracted_at, run_id
 FROM raw.mubi_festival_films
 ORDER BY festival_slug, year, page_num, extracted_at DESC NULLS LAST, run_id DESC
)
SELECT *, 'https://mubi.com/fr/awards-and-festivals/' || festival_slug || '?year=' || year || '&page=' || page_num AS lien
FROM pages ORDER BY extracted_at DESC NULLS LAST LIMIT 200""", display="table", col=0, row=34, size_x=24, size_y=9,
        description="Dernier état par édition/page, toutes origines historiques confondues, hors filtres films/période. Une page contient plusieurs films ; empty n’est pas une erreur."))
    return cards


def action_body(database_id, model_id, *, targeted=False):
    body = publisher.action_body(database_id, model_id, targeted=targeted)
    body["name"] = "Scraper un visa CNC sur Mubi" if targeted else "Demander un scraping Mubi"
    description = (
        "Airbyte → collecte Mubi CNC et éditions associées → dbt. "
        "Une seule demande de traitement active, partagée avec ingestion et Allociné. "
        "Les filtres du dashboard ne ciblent pas ce formulaire. "
        "Forcer ne concerne que le visa saisi et conserve l’historique."
    )
    body["description"] = description
    body["dataset_query"]["native"]["query"] = Path(__file__).with_name(
        "metabase-trigger-mubi-visa.sql" if targeted else "metabase-trigger-mubi.sql").read_text()
    body["visualization_settings"].update(name=body["name"], description=description)
    return body


def action_placement(action_id, dashcard_id, *, targeted=False):
    result = publisher.action_placement(action_id, dashcard_id, targeted=targeted)
    result["visualization_settings"]["button.label"] = "Scraper un visa CNC sur Mubi" if targeted else "Lancer le scraping Mubi"
    return result


if __name__ == "__main__":
    publisher.main(profile=sys.modules[__name__])
