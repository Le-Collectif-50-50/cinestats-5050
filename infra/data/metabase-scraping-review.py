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
EXECUTIONS_QUERY = QUERY.with_name("scraping_execution_status.sql")
REQUESTS_QUERY = QUERY.with_name("scraping_requests.sql")
ACTION_QUERY = ROOT / "infra/data/metabase-trigger-allocine.sql"
NAME = "Scraping Allociné — À examiner"
DESCRIPTION = (
    "Dernière tentative par identifiant source, lue directement dans raw.allocine_data. "
    "needs_review : correspondance non confirmée. visa_mismatch : visa Allociné différent du visa CNC. "
    "not_found : recherche sans résultat, à vérifier manuellement. "
    "Une tentative plus récente remplace le statut précédent. Les anciens résultats ne sont pas "
    "requalifiés automatiquement. Les filtres visa CNC et titre portent sur les films, "
    "pas sur le formulaire ni sur le suivi des demandes. "
    "Le graphique regroupe les tentatives par heure de Paris. Le filtre Période du scraping "
    "s'applique uniquement au graphique : sept derniers jours par défaut ; "
    "sans filtre, tout l'historique est affiché."
)
PARAMETERS = [
    {"id": "visa", "name": "Visa CNC", "slug": "visa", "type": "string/=", "sectionId": "string"},
    {"id": "titre", "name": "Titre contient", "slug": "titre", "type": "string/=", "sectionId": "string"},
    {"id": "periode", "name": "Période du scraping", "slug": "periode", "type": "date/relative",
     "sectionId": "date", "default": "past7days"},
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
                          display="scalar", col=index * 6, row=3, size_x=6, size_y=3))
    cards.append(dict(
        name="Statuts des films par heure", legacy_name="Statuts des films par exécution",
        query=EXECUTIONS_QUERY.read_text(encoding="utf-8"),
        display="bar", col=0, row=6, size_x=24, size_y=8,
        visualization_settings={
            "graph.dimensions": ["heure", "statut"], "graph.metrics": ["tentatives"],
            "stackable.stack_type": "stacked", "graph.x_axis.title_text": "Heure (Paris)",
            "graph.y_axis.title_text": "Tentatives enregistrées",
        },
        description="Toutes les tentatives stockées, y compris success, not_found, needs_review, "
                    "visa_mismatch, error et blocked. Résultats disponibles après écriture du lot ; "
                    "regroupement par heure de Paris (14:37 → 14:00), toutes exécutions confondues. "
                    "Période relative, sept derniers jours par défaut sur le dashboard ; sans filtre, tout l'historique. "
                    "Heures vides et dates nulles exclues.",
    ))
    cards.append(dict(
        name="Demandes de scraping Allociné", query=REQUESTS_QUERY.read_text(encoding="utf-8"),
        display="table", col=0, row=14, size_x=24, size_y=8,
        description="50 dernières demandes Metabase. Terminée signifie que le processus a fini, "
                    "même si certains films sont en erreur ou si aucun film n'était éligible pour un lot. "
                    "Par visa, Terminée exige un scraping confirmé puis dbt réussi. "
                    "Transmise / en cours inclut l'attente du worker. Hors filtres visa et titre.",
    ))
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
                          row=22 + index * 9, size_x=24, size_y=9))
    return cards


def dataset_query(database_id, query, extracted_at_field_id=None):
    tags = {p["id"]: {"id": p["id"], "name": p["id"], "display-name": p["name"],
                      "type": "text", "required": False} for p in PARAMETERS
            if "{{" + p["id"] + "}}" in query}
    if "periode" in tags:
        if extracted_at_field_id is None:
            raise ValueError("Le filtre période nécessite le champ Metabase raw.allocine_data.extracted_at.")
        tags["periode"].update(type="dimension", dimension=["field", extracted_at_field_id, None],
                               **{"widget-type": "date/relative"})
    return {"database": database_id, "type": "native",
            "native": {"query": query, "template-tags": tags}}


def action_body(database_id, model_id, *, targeted=False):
    fields = [
        ("email", "Votre nom ou adresse e-mail", "text", "string", None),
        ("reason", "Motif de la demande", "text", "text", None),
        ("max_films", "Nombre maximum de films", "number", "number", 10),
    ]
    if targeted:
        fields = fields[:2] + [
            ("visa_number", "Visa CNC", "text", "string", None),
            ("force_rescrape", "Forcer le retraitement", "text", "select", "Non"),
        ]
    action_name = "Scraper un visa CNC" if targeted else "Demander un scraping Allociné"
    description = (
        "Airbyte → scraping du visa saisi → dbt. Forcer rejoue aussi les traitements terminés. "
        "Les contrôles de correspondance restent actifs. Une seule demande Allociné active à la fois."
        if targeted else "Synchroniser les sources via Airbyte, puis traiter les films éligibles dans la limite demandée. "
        "Demander ensuite une ingestion pour publier les résultats. Une demande active à la fois."
    )
    tags, parameters, form_fields = {}, [], {}
    for order, (name, title, tag_type, input_type, default) in enumerate(fields):
        tag = {"id": name, "name": name, "display-name": title, "type": tag_type, "required": True}
        parameter = {"id": name, "name": title, "slug": name,
                     "type": "number/=" if tag_type == "number" else "string/=",
                     "target": ["variable", ["template-tag", name]]}
        if default is not None:
            tag["default"] = default
            parameter["default"] = default
        tags[name] = tag
        parameters.append(parameter)
        form_fields[name] = {"id": name, "name": name, "title": title, "order": order,
                             "inputType": input_type, "fieldType": "number" if tag_type == "number" else "string",
                             "required": True, "hidden": False, "width": "large"}
        if name == "force_rescrape":
            form_fields[name]["valueOptions"] = ["Non", "Oui"]
        if default is not None:
            form_fields[name]["defaultValue"] = default
            form_fields[name]["description"] = (
                "Retraiter ce visa même s’il a déjà été traité ; historique conservé."
                if name == "force_rescrape" else
                "Entier strictement positif ; les filtres du dashboard ne ciblent pas ce lancement."
            )
    return {
        "name": action_name, "type": "query", "model_id": model_id,
        "database_id": database_id,
        "description": description,
        "dataset_query": {"database": database_id, "type": "native", "native": {
            "query": (ACTION_QUERY.with_name("metabase-trigger-allocine-visa.sql") if targeted else ACTION_QUERY).read_text(encoding="utf-8"), "template-tags": tags}},
        "parameters": parameters,
        "visualization_settings": {
            "name": action_name, "type": "button", "fields": form_fields,
            "description": description,
            "submitButtonLabel": "Enregistrer la demande",
            "successMessage": "Demande enregistrée. Prise en charge au prochain passage du poller (environ 5 minutes).",
        },
    }


def action_placement(action_id, dashcard_id, *, targeted=False):
    return {"id": dashcard_id, "card_id": None, "action_id": action_id,
            "col": 12 if targeted else 0, "row": 0, "size_x": 12, "size_y": 2, "parameter_mappings": [],
            "visualization_settings": {
                "actionDisplayType": "button", "button.label": "Scraper un visa CNC" if targeted else "Lancer le scraping Allociné",
                "button.variant": "primary",
                "virtual_card": {"name": None, "display": "action", "visualization_settings": {},
                                 "dataset_query": {}, "archived": False},
            }}


def header_offset(dashboard):
    """Réserver les introductions et le lien métier existants au-dessus des boutons."""
    return max((card["row"] + card["size_y"] for card in dashboard.get("dashcards", [])
                if not card.get("card_id") and not card.get("action_id") and (
                    card.get("visualization_settings", {}).get("text", "").startswith("## Examiner le scraping Allociné")
                    or "Guide métier : revue humaine Allociné" in
                    card.get("visualization_settings", {}).get("text", ""))), default=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("METABASE_SITE_URL"))
    parser.add_argument("--env-file", type=Path, help="Fichier .env contenant METABASE_API_KEY (python-dotenv requis).")
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--database-name", default="cinestats-ops-db")
    parser.add_argument("--collection-id", type=int)
    parser.add_argument("--action-model-id", type=int,
                        help="Modèle Metabase de la file des demandes (38 sur Cinestats). Nécessite le poller migré.")
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
    metadata = api("GET", f"database/{database_id}/metadata")
    date_fields = [field["id"] for table in metadata["tables"]
                   if table["schema"] == "raw" and table["name"] == "allocine_data"
                   for field in table.get("fields", []) if field["name"] == "extracted_at"]
    if len(date_fields) != 1:
        parser.error("Champ raw.allocine_data.extracted_at absent ou ambigu : synchroniser le schéma Metabase.")
    extracted_at_field_id = date_fields[0]
    state = json.loads(args.state_file.read_text()) if args.state_file.exists() else {}
    if state and (state["url"] != base_url or state["database_id"] != database_id
                  or state.get("collection_id") != args.collection_id):
        parser.error("Le fichier d'état appartient à une autre instance, connexion ou collection.")
    model_id = args.action_model_id or state.get("action_model_id")
    if model_id:
        model = api("GET", f"card/{model_id}")
        if model.get("type") != "model" or model["dataset_query"]["database"] != database_id:
            parser.error("L'action doit utiliser un modèle de la même connexion Metabase.")

    # Vérifier droits et schéma avant toute création. Aucun résultat métier sauvé.
    for definition in definitions:
        result = api("POST", "dataset", dataset_query(database_id, definition["query"], extracted_at_field_id))
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
    offset = header_offset(dashboard)
    existing = {card["card_id"]: card for card in dashboard.get("dashcards", []) if card.get("card_id")}
    layout = []
    for index, definition in enumerate(definitions):
        name = definition["name"]
        body = {
            "name": "Scraping · " + name, "description": definition.get("description", DESCRIPTION),
            "display": definition["display"], "visualization_settings": definition.get("visualization_settings", {}),
            "dataset_query": dataset_query(database_id, definition["query"], extracted_at_field_id),
            "collection_id": args.collection_id,
        }
        legacy_name = definition.get("legacy_name")
        if name not in state["cards"] and legacy_name in state["cards"]:
            state["cards"][name] = state["cards"].pop(legacy_name)
            save_state()
        card_id = state["cards"].get(name)
        if card_id:
            api("PUT", f"card/{card_id}", body)
        else:
            card_id = api("POST", "card", body)["id"]
            state["cards"][name] = card_id
            save_state()
        placement = {field: definition[field] for field in ("col", "row", "size_x", "size_y")}
        placement["row"] += offset
        placement.update(id=existing.get(card_id, {}).get("id", -(index + 1)), card_id=card_id,
                         parameter_mappings=[{"parameter_id": p["id"], "card_id": card_id,
                                              "target": ["dimension" if p["id"] == "periode" else "variable",
                                                         ["template-tag", p["id"]]]}
                                             for p in PARAMETERS
                                             if p["id"] in body["dataset_query"]["native"]["template-tags"]])
        layout.append(placement)
    managed_ids = set(state["cards"].values())
    managed_action_ids = set()
    if model_id:
        for action_index, (state_key, targeted) in enumerate((("action_id", False), ("visa_action_id", True))):
            body = action_body(database_id, model_id, targeted=targeted)
            if state.get(state_key):
                api("PUT", f"action/{state[state_key]}", body)
            else:
                state[state_key] = api("POST", "action", body)["id"]
            state["action_model_id"] = model_id
            save_state()
            managed_action_ids.add(state[state_key])
            previous = next((c for c in dashboard.get("dashcards", [])
                             if c.get("action_id") == state[state_key]), {})
            placement = action_placement(state[state_key], previous.get("id", -(len(definitions) + 1 + action_index)),
                                         targeted=targeted)
            placement["row"] += offset
            layout.append(placement)
    layout.extend(card for card in dashboard.get("dashcards", [])
                  if card.get("card_id") not in managed_ids
                  and card.get("action_id") not in managed_action_ids)
    parameters = PARAMETERS + [p for p in dashboard.get("parameters", [])
                               if p["id"] not in {item["id"] for item in PARAMETERS}]
    api("PUT", f"dashboard/{dashboard_id}", {
        "name": NAME, "description": DESCRIPTION, "parameters": parameters, "dashcards": layout,
    })
    saved = api("GET", f"dashboard/{dashboard_id}")
    if not managed_ids.issubset({card.get("card_id") for card in saved.get("dashcards", [])}):
        raise SystemExit("Dashboard enregistré mais cartes incomplètes : relancer avec le même fichier d'état.")
    if not managed_action_ids.issubset({c.get("action_id") for c in saved.get("dashcards", [])}):
        raise SystemExit("Bouton absent après sauvegarde : relancer avec le même fichier d'état.")
    print(f"{base_url}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()
