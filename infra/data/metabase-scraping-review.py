#!/usr/bin/env python3
"""Créer ou actualiser le dashboard Metabase de revue du scraping Allociné."""

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
QUERY = ROOT / "ingestion/dbt/analyses/metabase/scraping_review_queue.sql"
NAME = "Scraping Allociné — À examiner"
DESCRIPTION = (
    "Dernière tentative par identifiant source, lue directement dans raw.allocine_data. "
    "needs_review : correspondance non confirmée. visa_mismatch : visa Allociné différent du visa CNC. "
    "not_found : recherche sans résultat, à vérifier manuellement. "
    "Une tentative plus récente remplace le statut précédent. Les anciens résultats ne sont pas "
    "requalifiés automatiquement. Les filtres visa CNC et titre s'appliquent à toutes les cartes."
)
PARAMETERS = [
    {"id": "visa", "name": "Visa CNC", "slug": "visa", "type": "string/=", "sectionId": "string"},
    {"id": "titre", "name": "Titre contient", "slug": "titre", "type": "string/=", "sectionId": "string"},
]


def dashboard_cards():
    prefix = QUERY.read_text(encoding="utf-8")
    cards = []
    for index, (name, condition) in enumerate([
        ("Films à examiner", "TRUE"),
        ("Correspondances à vérifier", "scrape_status = 'needs_review'"),
        ("Visas différents", "scrape_status = 'visa_mismatch'"),
        ("Films introuvables", "scrape_status = 'not_found'"),
    ]):
        cards.append(dict(name=name, query=prefix + f"SELECT COUNT(*) AS films FROM review_queue WHERE {condition}",
                          display="scalar", col=index * 6, row=0, size_x=6, size_y=3))
    for index, (name, status) in enumerate([
        ("Correspondances à vérifier — détails", "needs_review"),
        ("Visas différents — détails", "visa_mismatch"),
        ("Films introuvables — détails", "not_found"),
    ]):
        query = prefix + f"""
SELECT
    original_name AS titre_cnc,
    visa_number AS visa_cnc,
    allocine_title AS titre_allocine,
    allocine_visa_number AS visa_allocine,
    allocine_id,
    direction AS realisation_allocine,
    error_message AS motif,
    extracted_at AT TIME ZONE 'Europe/Paris' AS derniere_tentative_paris,
    match_strategy AS strategie,
    COALESCE(NULLIF(allocine_url, ''), NULLIF(source_url, '')) AS lien_allocine,
    search_url AS lien_recherche,
    source_record_id AS identifiant_source,
    run_id AS execution,
    scrape_status AS statut
FROM review_queue
WHERE scrape_status = '{status}'
ORDER BY extracted_at ASC NULLS FIRST, source_record_id, record_hash
"""
        cards.append(dict(name=name, query=query, display="table", col=0,
                          row=3 + index * 9, size_x=24, size_y=9))
    return cards


def dataset_query(database_id, query):
    tags = {p["id"]: {"id": p["id"], "name": p["id"], "display-name": p["name"],
                      "type": "text", "required": False} for p in PARAMETERS}
    return {"database": database_id, "type": "native",
            "native": {"query": query, "template-tags": tags}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("METABASE_SITE_URL"))
    parser.add_argument("--env-file", type=Path, help="Fichier .env contenant METABASE_API_KEY (python-dotenv requis).")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--database-name", default="cinestats-ops-db")
    parser.add_argument("--collection-id", type=int)
    parser.add_argument("--state-file", type=Path, default=ROOT / "ingestion/scraping/allocine/local-runs/metabase-review-state.json")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--check", action="store_true", help="Exécuter les requêtes sans créer de dashboard.")
    args = parser.parse_args()
    definitions = dashboard_cards()
    if args.preview:
        print(json.dumps(definitions, ensure_ascii=False, indent=2))
        return
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
    base_url = (args.url or os.environ.get("METABASE_SITE_URL", "")).rstrip("/")
    key = args.api_key_file.read_text().strip() if args.api_key_file else os.environ.get("METABASE_API_KEY")
    if not base_url.startswith("https://") or not key:
        parser.error("Une URL HTTPS et une clé API Metabase sont requises.")

    def api(method, path, data=None):
        request = Request(base_url + "/api/" + path, method=method,
                          headers={"x-api-key": key, "Content-Type": "application/json"},
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            raise SystemExit(f"Metabase : {method} {path}, HTTP {error.code}.") from None
        except URLError:
            raise SystemExit("Metabase inaccessible : vérifier URL, réseau et certificat TLS.") from None

    databases = api("GET", "database")
    matches = [db for db in databases["data"] if db["name"] == args.database_name]
    if len(matches) != 1:
        parser.error("Connexion Metabase absente ou ambiguë.")
    database_id = matches[0]["id"]
    state = json.loads(args.state_file.read_text()) if args.state_file.exists() else {}
    if state and (state["url"] != base_url or state["database_id"] != database_id
                  or state.get("collection_id") != args.collection_id):
        parser.error("Le fichier d'état appartient à une autre instance, connexion ou collection.")

    # Vérifier droits et schéma avant toute création. Aucun résultat métier sauvé.
    for definition in definitions:
        result = api("POST", "dataset", dataset_query(database_id, definition["query"]))
        if result.get("status") != "completed":
            raise SystemExit(f"Requête en échec : {definition['name']}. {result.get('error', '')}")
        rows = result.get("data", {}).get("rows", [])
        metric = f" : {rows[0][0]}" if definition["display"] == "scalar" and rows else ""
        print(f"Vérifié : {definition['name']}{metric}")
    if args.check:
        return

    def save_state():
        args.state_file.parent.mkdir(parents=True, exist_ok=True)
        args.state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    if not state:
        dashboard = api("POST", "dashboard", {
            "name": NAME, "description": DESCRIPTION,
            "collection_id": args.collection_id, "parameters": PARAMETERS,
        })
        state = dict(url=base_url, database_id=database_id, collection_id=args.collection_id,
                     dashboard_id=dashboard["id"], cards={})
        save_state()

    dashboard_id = state["dashboard_id"]
    dashboard = api("GET", f"dashboard/{dashboard_id}")
    existing = {card["card_id"]: card for card in dashboard.get("dashcards", []) if card.get("card_id")}
    layout = []
    for index, definition in enumerate(definitions):
        name = definition["name"]
        body = {
            "name": "Scraping · " + name, "description": DESCRIPTION,
            "display": definition["display"], "visualization_settings": {},
            "dataset_query": dataset_query(database_id, definition["query"]),
            "collection_id": args.collection_id,
        }
        card_id = state["cards"].get(name)
        if card_id:
            api("PUT", f"card/{card_id}", body)
        else:
            card_id = api("POST", "card", body)["id"]
            state["cards"][name] = card_id
            save_state()
        placement = {field: definition[field] for field in ("col", "row", "size_x", "size_y")}
        placement.update(id=existing.get(card_id, {}).get("id", -(index + 1)), card_id=card_id,
                         parameter_mappings=[{"parameter_id": p["id"], "card_id": card_id,
                                              "target": ["variable", ["template-tag", p["id"]]]}
                                             for p in PARAMETERS])
        layout.append(placement)
    managed_ids = set(state["cards"].values())
    layout.extend(card for card in dashboard.get("dashcards", []) if card.get("card_id") not in managed_ids)
    parameters = PARAMETERS + [p for p in dashboard.get("parameters", [])
                               if p["id"] not in {item["id"] for item in PARAMETERS}]
    api("PUT", f"dashboard/{dashboard_id}", {
        "name": NAME, "description": DESCRIPTION, "parameters": parameters, "dashcards": layout,
    })
    saved = api("GET", f"dashboard/{dashboard_id}")
    if not managed_ids.issubset({card.get("card_id") for card in saved.get("dashcards", [])}):
        raise SystemExit("Dashboard enregistré mais cartes incomplètes : relancer avec le même fichier d'état.")
    print(f"{base_url}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()
