#!/usr/bin/env python3
"""Créer ou actualiser le dashboard dbt via une clé API Metabase explicite."""

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
QUERIES = ROOT / "ingestion/dbt/analyses/metabase"


def dashboard_cards():
    """Définition versionnée ; aucun accès réseau ni secret pour la prévisualiser."""
    cards = []
    metrics = [
        ("Tests en avertissement", "SELECT COUNT(*) FROM ops.v_dbt_latest_results WHERE status = 'warn'"),
        ("Erreurs bloquantes", "SELECT COUNT(*) FROM ops.v_dbt_latest_results WHERE status IN ('fail', 'error')"),
        ("Crédits isolés", "SELECT COUNT(*) FROM ops.film_credits_unmatched"),
    ]
    for index, (name, query) in enumerate(metrics):
        cards.append(dict(name=name, query=query, display="scalar", col=index * 8, row=0, size_x=8, size_y=3))
    for index, (name, filename) in enumerate([
        ("Contrôles à examiner", "latest_warnings.sql"),
        ("Correspondances source à revoir", "matching_duplicate_details.sql"),
        ("Détails des anomalies", "latest_failure_details.sql"),
        ("Historique des exécutions", "run_history.sql"),
    ]):
        cards.append(dict(name=name, query=(QUERIES / filename).read_text(), display="table",
                          col=0, row=3 + index * 7, size_x=24, size_y=7))
    return cards


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("METABASE_SITE_URL"))
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--database-name", default="cinestats-ops-db")
    parser.add_argument("--collection-id", type=int)
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--preview", action="store_true", help="Afficher les cartes sans appeler Metabase.")
    args = parser.parse_args()
    definitions = dashboard_cards()
    if args.preview:
        print(json.dumps(definitions, ensure_ascii=False, indent=2))
        return
    if not args.url or not args.api_key_file or not args.state_file:
        parser.error("--url, --api-key-file et --state-file sont requis hors prévisualisation")
    base_url = args.url.rstrip("/")
    key = args.api_key_file.read_text().strip()
    if not key:
        parser.error("Le fichier de clé API est vide")

    def api(method, path, data=None):
        request = Request(base_url + "/api/" + path, method=method,
                          headers={"x-api-key": key, "Content-Type": "application/json"},
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            raise SystemExit(f"Metabase : {method} {path}, HTTP {error.code}. Vérifier droits et paramètres.") from None

    databases = api("GET", "database")
    matches = [database for database in databases["data"] if database["name"] == args.database_name]
    if len(matches) != 1:
        parser.error("La connexion Metabase demandée est absente ou ambiguë")
    database_id = matches[0]["id"]
    state = json.loads(args.state_file.read_text()) if args.state_file.exists() else {}
    if state and (state["url"] != base_url or state["database_id"] != database_id):
        parser.error("Le fichier d'état appartient à une autre instance ou connexion")

    def save_state():
        args.state_file.parent.mkdir(parents=True, exist_ok=True)
        args.state_file.write_text(json.dumps(state, indent=2))

    if not state:
        dashboard = api("POST", "dashboard", {
            "name": "Qualité des données — dbt",
            "description": "Dernier résultat de chaque contrôle dbt, détails des anomalies et historique. Les avertissements ne bloquent pas l'ingestion. Les crédits sans film sont isolés.",
            "collection_id": args.collection_id,
            "parameters": [],
        })
        state = dict(url=base_url, database_id=database_id, dashboard_id=dashboard["id"], cards={})
        save_state()

    dashboard_id = state["dashboard_id"]
    dashboard = api("GET", f"dashboard/{dashboard_id}")
    existing = {card["card_id"]: card for card in dashboard.get("dashcards", []) if card.get("card_id")}
    layout = []
    for index, definition in enumerate(definitions):
        name = definition["name"]
        card_body = {
            "name": "dbt · " + name,
            "description": "Géré par infra/data/metabase-dbt-quality.py",
            "display": definition["display"],
            "visualization_settings": {},
            "dataset_query": {"database": database_id, "type": "native", "native": {"query": definition["query"]}},
            "collection_id": args.collection_id,
        }
        card_id = state["cards"].get(name)
        if card_id:
            api("PUT", f"card/{card_id}", card_body)
        else:
            card_id = api("POST", "card", card_body)["id"]
            state["cards"][name] = card_id
            save_state()
        placement = {field: definition[field] for field in ("col", "row", "size_x", "size_y")}
        placement.update(id=existing.get(card_id, {}).get("id", -(index + 1)), card_id=card_id,
                         parameter_mappings=[])
        layout.append(placement)
    # Préserver les cartes ajoutées manuellement sur ce dashboard.
    managed_ids = set(state["cards"].values())
    layout.extend(card for card in dashboard.get("dashcards", []) if card.get("card_id") not in managed_ids)
    api("PUT", f"dashboard/{dashboard_id}/cards", {"cards": layout})
    print(f"{base_url}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()
