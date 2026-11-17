#!/usr/bin/env python3
"""Réconcilier les dashboards Operations de Cinestats, sans lancer d'ingestion."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE = "https://metabase.cinestats5050.fr"
NAMES = {2: "Pipeline Overview", 3: "Qualité des données — dbt",
         7: "Scraping Allociné — À examiner", 11: "Suivi des données par visa CNC"}
LINKS = (
    "[Pipeline Overview](/dashboard/2) · [Qualité dbt](/dashboard/3) · "
    "[Scraping Allociné](/dashboard/7) · [Suivi par visa CNC](/dashboard/11) · "
    "[Fiche Film](/dashboard/9)"
)
INTRO = {
    2: """## Piloter l’ingestion
Le bouton enregistre une demande : synchronisation Airbyte, puis transformations et contrôles dbt. Le poller la prend en charge au prochain passage (environ 5 minutes).

**Le scraping se demande depuis le dashboard Allociné.** Le bouton par visa synchronise les sources, collecte ce film puis publie les résultats. Après un scraping par lot, demander une ingestion pour publier ses résultats.

Ce suivi couvre uniquement les demandes d’ingestion enregistrées dans Metabase. Les lancements manuels Prefect ne figurent pas ici. Un statut `success` indique une exécution terminée ; consulter la qualité dbt pour les avertissements.""",
    3: """## Lire les contrôles dbt
Sans filtre, chaque contrôle affiche son dernier résultat connu : plusieurs exécutions peuvent être représentées. Avec **Heure d’exécution**, les résultats concernent l’exécution choisie, en heure de Paris.

Les avertissements ne bloquent pas l’ingestion. Les crédits isolés comptent des lignes de crédits, pas des films ; une valeur vide sur un run signifie que le contrôle n’y est pas disponible. Les correspondances source à revoir utilisent le matching **actuel**, même pour un run ancien.

Les détails peuvent dépasser la limite d’affichage Metabase. Une ingestion en cours peut rendre certaines tables temporairement indisponibles ; actualiser après sa fin.

""" + LINKS,
    7: """## Examiner le scraping Allociné
Les compteurs et détails montrent la dernière tentative par identifiant source pour trois statuts : correspondance à vérifier, visa différent et recherche sans résultat. Ils ne recensent pas les erreurs techniques `error` / `blocked`.

Le graphique compte **des tentatives, pas des films distincts**, par heure de Paris, tous statuts inclus. Le filtre **Période du scraping** ne concerne que ce graphique ; les compteurs restent sur tout l’historique. Visa et titre filtrent les films, jamais le formulaire ni les demandes.

**Scraper un visa CNC** : saisir explicitement le visa, votre identité et le motif. **Forcer le retraitement** propose Non par défaut ; Oui rejoue ce visa même s’il est déjà traité. Le parcours synchronise les sources, collecte uniquement ce visa, puis publie les résultats. Un résultat non confirmé arrête le traitement ; le forçage ne remplace pas la vérification d’identité.

**Lancer le scraping Allociné** : synchroniser les sources via Airbyte, puis traiter un lot de films éligibles, dans la limite demandée. Les filtres du dashboard ne ciblent pas ce lot. Une demande terminée ne garantit pas le succès de chaque film ; demander ensuite une ingestion pour publier les résultats.

Les deux boutons partagent une seule demande Allociné active. Suivre la table des demandes et son message d’erreur éventuel.

""" + LINKS,
    11: """## Suivre un visa CNC
Choisir un visa exact dans le filtre. Source synchronisée → matching → scraping → staging → transformations → modèles finaux.

**Dernier essai ≠ dernier succès ≠ données publiées.** Les valeurs vides restent inconnues. Les tables dbt reflètent leur dernière reconstruction ; le snapshot Airbyte peut différer du GSheet actuel. Une concordance des identifiants ne valide pas l’identité de l’œuvre.

Pendant une ingestion, certaines tables peuvent être temporairement indisponibles. Actualiser après sa fin.

""" + LINKS,
}
QUERIES = {
    43: ("Ingestion · Statut de la dernière demande", "scalar", """
SELECT COALESCE((SELECT request_status FROM ops.ingestion_run_requests
WHERE request_type = 'ingestion'
ORDER BY requested_at DESC, request_id DESC LIMIT 1), 'Aucune demande') AS statut
"""),
    44: ("Ingestion · Demandes par heure et statut", "bar", """
SELECT DATE_TRUNC('hour', requested_at AT TIME ZONE 'UTC'
                  AT TIME ZONE 'Europe/Paris') AS heure_paris,
       request_status AS statut, COUNT(*) AS demandes
FROM ops.ingestion_run_requests
WHERE request_type = 'ingestion'
GROUP BY 1, 2 ORDER BY 1, 2
"""),
    45: ("Ingestion · Dernière demande — détails", "table", """
SELECT requested_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Paris' AS demande_le_paris,
       request_status AS statut,
       processed_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Paris' AS terminee_le_paris,
       COALESCE(NULLIF(trigger_error, ''), 'Aucune erreur signalée') AS message,
       triggered_flow_run_id AS execution_prefect, request_id AS demande_id
FROM ops.ingestion_run_requests
WHERE request_type = 'ingestion'
ORDER BY requested_at DESC, request_id DESC LIMIT 1
"""),
}


def text_card(identifier, text, row=0, height=7):
    return dict(id=identifier, card_id=None, row=row, col=0, size_x=24, size_y=height,
                parameter_mappings=[], visualization_settings={
                    "virtual_card": {"name": None, "display": "text", "dataset_query": {},
                                     "archived": False, "visualization_settings": {}},
                    "text": text})


def layout(dashboard):
    did = dashboard["id"]
    cards = deepcopy(dashboard["dashcards"])
    # Préserver le raccourci métier publié indépendamment du layout des indicateurs.
    tutorial_cards = [c for c in cards if not c.get("card_id") and
                      "Guide métier : revue humaine Allociné" in
                      c.get("visualization_settings", {}).get("text", "")]
    cards = [c for c in cards if c not in tutorial_cards]
    if did == 2:
        # Metabase archive les questions propres au dashboard lors de leur retrait.
        cards = [c for c in cards if c.get("card_id") not in {39, 40, 41, 46}
                 and c["id"] not in {39, 43}]
        positions = {36: (9, 0, 8, 3), 37: (9, 8, 16, 3),
                     42: (12, 0, 24, 7), 44: (19, 0, 24, 5)}
        for c in cards:
            if c["id"] in positions:
                c.update(zip(("row", "col", "size_x", "size_y"), positions[c["id"]], strict=True))
                c["parameter_mappings"] = []
                if c.get("card_id"):
                    c["visualization_settings"] = {}
                else:
                    c["visualization_settings"]["button.label"] = "Demander une ingestion"
        cards += [text_card(39, INTRO[2], height=5), text_card(43,
            "## Poursuivre le diagnostic\n"
            "- [Qualité dbt](/dashboard/3) : contrôles, anomalies et historique.\n"
            "- [Scraping Allociné](/dashboard/7) : lancer et examiner les tentatives.\n"
            "- [Suivi par visa CNC](/dashboard/11) : comprendre la propagation d’un film.\n"
            "- [Fiche Film](/dashboard/9) : consulter les données finales.", row=5, height=4)]
    else:
        heading = INTRO[did].splitlines()[0]
        previous = next((c for c in cards if not c.get("card_id")
                         and not c.get("action_id") and
                         c.get("visualization_settings", {}).get("text", "").startswith(heading)), None)
        if previous:
            cards.remove(previous)
        offset = 7 - min((c["row"] for c in cards), default=0)
        for c in cards:
            c["row"] += offset
        cards.append(text_card(previous["id"] if previous else -1000, INTRO[did]))
    if tutorial_cards:
        for card in cards:
            card["row"] += 2
        guide = tutorial_cards[0]
        guide.update(row=0, col=0, size_x=24, size_y=2)
        cards.append(guide)
    return cards


def period_query(card, parameter):
    """Aligner le widget de la question sur le filtre temporel du dashboard."""
    query = deepcopy(card["dataset_query"])
    tag = next(t for t in query["stages"][0]["template-tags"] if t["name"] == "periode")
    tag["widget-type"] = parameter["type"]
    parameters = []
    if parameter.get("default"):
        parameters.append({"id": tag["id"], "type": parameter["type"],
                           "target": ["dimension", ["template-tag", "periode"]],
                           "value": parameter["default"]})
    return query, parameters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--apply", action="store_true", help="Appliquer après vérification SQL.")
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
    key = os.environ.get("METABASE_API_KEY")
    if not key:
        parser.error("METABASE_API_KEY est requise.")

    def api(method, path, data=None):
        request = Request(BASE + "/api/" + path, method=method,
                          headers={"x-api-key": key, "Content-Type": "application/json"},
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            with urlopen(request, timeout=90) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            raise SystemExit(f"Metabase : {method} {path}, HTTP {error.code}.") from None

    dashboards = {did: api("GET", f"dashboard/{did}") for did in NAMES}
    for did, dashboard in dashboards.items():
        if dashboard["name"] != NAMES[did] or dashboard["collection_id"] != 7:
            raise SystemExit(f"Dashboard {did} inattendu ; aucune modification.")
    db = api("GET", "database/3")
    if db["name"] != "cinestats-ops-db":
        raise SystemExit("Connexion inattendue ; aucune modification.")
    for cid, (_, _, sql) in QUERIES.items():
        result = api("POST", "dataset", {"database": 3, "type": "native", "native": {"query": sql}})
        if result.get("status") != "completed":
            raise SystemExit(f"Question {cid} : vérification SQL en échec.")
        print(f"Question {cid} : SQL vérifié.", flush=True)
    period = next(p for p in dashboards[7]["parameters"] if p["id"] == "periode")
    hourly_card = api("GET", "card/83")
    hourly_query, parameters = period_query(hourly_card, period)
    result = api("POST", "dataset", dict(hourly_query, parameters=parameters))
    if result.get("status") != "completed":
        raise SystemExit("Question 83 : filtre de période en échec.")
    print("Question 83 : filtre de période vérifié.", flush=True)
    planned = {did: layout(d) for did, d in dashboards.items()}
    for did, cards in planned.items():
        print(f"{NAMES[did]} : {len(cards)} cartes, introduction et navigation.", flush=True)
    if not args.apply:
        print("Vérification seule ; utiliser --apply pour enregistrer.")
        return
    if hourly_query != hourly_card["dataset_query"]:
        api("PUT", "card/83", {"dataset_query": hourly_query})
    for cid, (name, display, sql) in QUERIES.items():
        settings = {"table.pivot": False} if display == "table" else {}
        if display == "bar":
            settings = {"graph.dimensions": ["heure_paris", "statut"], "graph.metrics": ["demandes"],
                        "stackable.stack_type": "stacked", "graph.x_axis.title_text": "Heure de demande (Paris)",
                        "graph.y_axis.title_text": "Nombre de demandes", "graph.x_axis.scale": "ordinal"}
        api("PUT", f"card/{cid}", {"name": name, "display": display,
            "description": "Demandes Metabase de type ingestion uniquement. Hors scraping et lancements manuels Prefect. "
                           "Le statut enregistré ne mesure pas la qualité des données ni une progression en direct.",
            "dataset_query": {"database": 3, "type": "native", "native": {"query": sql}},
            "visualization_settings": settings})
    for did, cards in planned.items():
        body = {"dashcards": cards, "description": INTRO[did]}
        if did == 2:
            body["parameters"] = []
        api("PUT", f"dashboard/{did}", body)
        saved = api("GET", f"dashboard/{did}")
        assert len(saved["dashcards"]) == len(cards)
        assert any(c.get("visualization_settings", {}).get("text") == INTRO[did]
                   for c in saved["dashcards"])
        print(f"Enregistré et relu : {BASE}/dashboard/{did}", flush=True)


if __name__ == "__main__":
    main()
