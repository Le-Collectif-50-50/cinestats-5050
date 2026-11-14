#!/usr/bin/env python3
"""Publier le suivi de provenance par visa CNC dans Metabase Operations."""

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
NAME = "Suivi des données par visa CNC"
PREFIX = """WITH p AS (SELECT {{visa}}::text AS visa),
ids AS (SELECT md5(visa)::uuid AS film_id FROM p),
matching AS (SELECT m.* FROM raw.id_matching m, p WHERE btrim(m."VISA"::text)=p.visa),
attempts AS (SELECT a.* FROM raw.allocine_data a,p WHERE a.visa_number::text=p.visa),
last_attempt AS (SELECT * FROM attempts ORDER BY extracted_at DESC NULLS LAST, run_id::text DESC, record_hash DESC LIMIT 1),
last_success AS (SELECT * FROM attempts WHERE scrape_status='success' ORDER BY extracted_at DESC NULLS LAST, run_id::text DESC, record_hash DESC LIMIT 1)
"""


def definitions():
    cards = []

    def add(name, query, description, height=7):
        cards.append(
            dict(name=name, query=PREFIX + query, description=description, height=height)
        )

    add(
        "État de propagation",
        """SELECT p.visa AS visa_cnc,
 (SELECT count(*) FROM raw.films r WHERE to_jsonb(r)->>'VISA'=p.visa) AS lignes_cnc,
 (SELECT count(*) FROM matching) AS lignes_matching,
 (SELECT string_agg(DISTINCT "ID_ALLOCINE"::text, ', ') FROM matching) AS ids_cibles,
 (SELECT extracted_at FROM last_attempt) AS dernier_essai,
 (SELECT scrape_status FROM last_attempt) AS statut_dernier_essai,
 (SELECT allocine_id FROM last_attempt) AS id_dernier_essai,
 (SELECT extracted_at FROM last_success) AS dernier_succes,
 (SELECT allocine_id FROM last_success) AS id_dernier_succes,
 (SELECT string_agg(DISTINCT s.allocine_id, ', ') FROM staging.stg_allocine_films s WHERE s.cnc_visa::text=p.visa) AS ids_staging,
 (SELECT count(*) FROM intermediate.int_allocine_films a JOIN ids USING(film_id)) AS films_allocine_rattaches,
 (SELECT count(*) FROM fnl.fnl_films f WHERE f.cnc_visa::text=p.visa) AS films_finaux,
 CASE WHEN NOT EXISTS(SELECT 1 FROM matching) THEN 'Matching absent'
 WHEN (SELECT count(*) FROM matching)>1 THEN 'Plusieurs lignes de matching : examiner les doublons'
 WHEN NOT EXISTS(SELECT 1 FROM last_success) THEN 'Aucun succès de scraping'
 WHEN NOT EXISTS(SELECT 1 FROM last_success s JOIN matching m ON btrim(m."ID_ALLOCINE"::text)=s.allocine_id::text) THEN 'Dernier succès différent du matching courant'
 WHEN NOT EXISTS(SELECT 1 FROM staging.stg_allocine_films s JOIN matching m ON btrim(m."ID_ALLOCINE"::text)=s.allocine_id WHERE s.cnc_visa::text=p.visa) THEN 'Staging absent ou différent du matching courant'
 WHEN NOT EXISTS(SELECT 1 FROM intermediate.int_allocine_films a JOIN ids USING(film_id)) THEN 'Rattachement intermédiaire absent'
 ELSE 'Identifiant propagé : vérifier identité, dates, genres et crédits' END AS controle
 FROM p""",
        "Diagnostic technique ; une concordance des identifiants ne valide pas l’identité de l’œuvre.",
        5,
    )

    def fields(name, sources, desc):
        union = " UNION ALL ".join(
            f"SELECT '{table}'::text AS source, to_jsonb(t) AS donnees FROM {table} t WHERE {where}"
            for table, where in sources
        )
        add(
            name,
            f"""SELECT source, dense_rank() OVER (PARTITION BY source ORDER BY donnees::text) AS ligne,
 kv.key AS champ, kv.value AS valeur FROM ({union}) rows
 CROSS JOIN LATERAL jsonb_each_text(donnees) kv ORDER BY source, ligne, champ""",
            desc,
        )

    visa = "t.cnc_visa::text=(SELECT visa FROM p)"
    fid = "t.film_id IN (SELECT film_id FROM ids)"
    fields(
        "01 · Ligne CNC synchronisée",
        [("raw.films", "btrim(to_jsonb(t)->>'VISA')=(SELECT visa FROM p)")],
        "Toutes les colonnes du snapshot Airbyte courant, métadonnées incluses. Ce snapshot ne prouve pas le contenu actuel du GSheet ni le fichier CNC historique.",
    )
    fields(
        "02 · Matching courant",
        [("raw.id_matching", "t IN (SELECT m FROM matching m)")],
        "Toutes les lignes présentes pour le visa, sans masquer les doublons ; validation manuelle et métadonnées Airbyte incluses.",
    )
    fields(
        "03 · Dernier essai Allociné",
        [("last_attempt", "true")],
        "Dernier essai tous statuts, même en erreur. Ordre : extracted_at, run_id, record_hash décroissants ; timestamps NULL en dernier.",
    )
    fields(
        "04 · Dernier succès Allociné",
        [("last_success", "true")],
        "Dernier succès par visa, indépendamment du matching courant. Un succès ancien peut concerner une autre fiche : examiner le contrôle de propagation.",
    )
    fields(
        "05 · Staging CNC et matching",
        [("staging.stg_cnc_films", visa), ("staging.stg_id_matching", visa)],
        "Données réellement matérialisées ; filtres de métadonnées du matching appliqués par dbt.",
    )
    fields(
        "06 · Staging Allociné",
        [("staging.stg_allocine_films", visa)],
        "Dernier succès retenu lors de la dernière reconstruction dbt, avec run, hash, dates et crédits source.",
    )
    fields(
        "07 · Transformations des films",
        [
            ("intermediate.int_id_matching", visa),
            ("intermediate.int_cnc_films", visa),
            ("intermediate.int_allocine_films", fid),
        ],
        "Matching, règles CNC et rattachement Allociné. Une fiche non rattachée reste visible dans le staging.",
    )
    add(
        "08 · Crédits transformés",
        """SELECT t.* FROM intermediate.int_credit_holders_role t WHERE t.film_id IN (SELECT film_id FROM ids) ORDER BY role, full_name, credit_holder_id""",
        "Tous les crédits rattachés : nom complet source, rôle, identifiants de personne et Allociné.",
        9,
    )
    fields(
        "09 · Genres et financements transformés",
        [
            ("intermediate.int_film_genres", visa),
            ("intermediate.int_film_country_budget_allocation", visa),
        ],
        "Toutes les associations intermédiaires, distinctes des corrections et des modèles finaux.",
    )
    fields(
        "10 · Corrections manuelles appliquées",
        [
            (f"staging.{t}", fid)
            for t in [
                "stg_fix_film_credits",
                "stg_fix_film_genres",
                "stg_fix_film_country_budget_allocation",
            ]
        ]
        + [
            (
                "staging.stg_fix_credit_holders",
                "t.id IN (SELECT credit_holder_id FROM intermediate.int_credit_holders_role WHERE film_id IN (SELECT film_id FROM ids) UNION SELECT credit_holder_id FROM fnl.fnl_film_credits WHERE film_id IN (SELECT film_id FROM ids))",
            )
        ],
        "Corrections staging du film et des personnes créditées, avec auteur et date si disponibles. Une section vide signifie aucune correction correspondante.",
    )
    fields(
        "11 · Film final et affiche",
        [("fnl.fnl_films", visa), ("fnl.fnl_film_posters", visa)],
        "Toutes les colonnes publiées du film final et de son affiche.",
    )
    add(
        "12 · Crédits et personnes finaux",
        """SELECT c.*, r.role_inclusive_name, r.role_name, r.is_key_role,
 h.type, h.first_name, h.last_name, h.legal_name, h.gender, h.birthdate
 FROM fnl.fnl_film_credits c LEFT JOIN fnl.fnl_role r USING(role_id)
 LEFT JOIN fnl.fnl_credit_holders h USING(credit_holder_id)
 WHERE c.film_id IN (SELECT film_id FROM ids)
 ORDER BY r.is_key_role DESC NULLS LAST, r.role_name, h.last_name""",
        "Une ligne par association publiée personne/société × rôle. Vérifier en particulier la réalisation pour le visa 144246.",
        10,
    )
    add(
        "13 · Genres finaux",
        """SELECT fg.*,g.genre_name FROM fnl.fnl_film_genre fg LEFT JOIN fnl.fnl_genre g USING(genre_id) WHERE fg.film_id IN (SELECT film_id FROM ids) ORDER BY g.genre_name""",
        "Genres cinématographiques publiés ; une absence de ligne est visible sans fallback legacy.",
        5,
    )
    fields(
        "14 · Financements finaux",
        [("fnl.fnl_film_country_budget_allocation", fid)],
        "Toutes les répartitions finales par pays.",
    )
    add(
        "15 · Historique récent des essais",
        """SELECT extracted_at,run_id,allocine_id,allocine_title,scrape_status,match_strategy,error_message,record_hash FROM attempts ORDER BY extracted_at DESC NULLS LAST, run_id::text DESC,record_hash DESC LIMIT 30""",
        "Les 30 essais les plus récents pour contextualiser le dernier état ; les autres sections montrent les données courantes.",
        8,
    )
    fields(
        "16 · Enrichissements Mubi transformés",
        [
            ("intermediate.int_mubi_festival_films", visa),
            ("intermediate.int_mubi_film_awards", visa),
        ],
        "Dernières tables Mubi matérialisées pour le visa ; festivals et récompenses ne sont pas reconstruits à la consultation.",
    )
    add(
        "17 · Crédits en quarantaine liés au matching",
        """SELECT t.* FROM ops.film_credits_unmatched t WHERE t.allocine_id::text IN (SELECT btrim("ID_ALLOCINE"::text) FROM matching UNION SELECT allocine_id::text FROM attempts) ORDER BY allocine_id, role, full_name""",
        "Crédits non publiés associés aux identifiants courants ou historiques du visa. Un identifiant partagé peut concerner une autre œuvre : ce lien est à vérifier.",
        7,
    )
    return cards


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://metabase.cinestats5050.fr")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv

        load_dotenv(args.env_file)
    key = os.environ["METABASE_API_KEY"]

    def api(method, path, data=None):
        req = Request(
            args.url.rstrip("/") + "/api/" + path,
            method=method,
            headers={"x-api-key": key, "Content-Type": "application/json"},
            data=json.dumps(data).encode() if data is not None else None,
        )
        with urlopen(req, timeout=90) as r:
            return json.load(r)

    dbs = [d for d in api("GET", "database")["data"] if d["name"] == "cinestats-ops-db"]
    assert len(dbs) == 1
    db = dbs[0]["id"]

    def query(sql, value=None):
        q = {
            "database": db,
            "type": "native",
            "native": {
                "query": sql,
                "template-tags": {
                    "visa": {
                        "id": "visa",
                        "name": "visa",
                        "display-name": "Visa CNC",
                        "type": "text",
                        "required": True,
                        "default": "144246",
                    }
                },
            },
        }
        if value is not None:
            q["parameters"] = [
                {
                    "type": "category",
                    "target": ["variable", ["template-tag", "visa"]],
                    "value": value,
                }
            ]
        return q

    cards = definitions()
    from concurrent.futures import ThreadPoolExecutor

    def check(card):
        r = api("POST", "dataset", query(card["query"], "144246"))
        if r.get("status") != "completed":
            raise RuntimeError(card["name"] + ": " + str(r.get("error")))
        print(card["name"], len(r["data"]["rows"]), "lignes : OK", flush=True)
        if card == cards[0]:
            print("Diagnostic", r["data"]["rows"], flush=True)

    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(check, cards))
    if args.check:
        return
    collections = [
        c for c in api("GET", "collection") if c["name"] == "Cinestats 50/50 - Operations"
    ]
    assert len(collections) == 1
    cid = collections[0]["id"]
    items = api("GET", f"collection/{cid}/items")["data"]
    dashboards = [i for i in items if i["model"] == "dashboard" and i["name"] == NAME]
    assert len(dashboards) <= 1
    params = [
        {
            "id": "visa",
            "name": "Visa CNC",
            "slug": "visa",
            "type": "string/=",
            "default": ["144246"],
            "required": True,
            "sectionId": "string",
        }
    ]
    dash = (
        api("GET", f"dashboard/{dashboards[0]['id']}")
        if dashboards
        else api(
            "POST", "dashboard", {"name": NAME, "collection_id": cid, "parameters": params}
        )
    )
    existing = {c["card_id"]: c for c in dash.get("dashcards", []) if c.get("card_id")}
    intro = "## Suivre un visa CNC\nVisa exact, par défaut **144246**. Source synchronisée → matching → scraping → staging → transformations → modèles finaux.\n\n**Dernier essai ≠ dernier succès ≠ données publiées.** Les sections détaillées exposent toutes les colonnes disponibles ; les valeurs vides restent inconnues. Les tables dbt reflètent leur dernière reconstruction. Le snapshot Airbyte peut différer du GSheet actuel.\n\nPour [#46](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/46), vérifier fiche, nature de l’œuvre, date, genres et réalisation. Une identité concordante ne constitue pas une validation métier automatique."
    layout = [
        {
            "id": -100,
            "card_id": None,
            "row": 0,
            "col": 0,
            "size_x": 24,
            "size_y": 5,
            "parameter_mappings": [],
            "visualization_settings": {
                "virtual_card": {
                    "name": None,
                    "display": "text",
                    "dataset_query": {},
                    "archived": False,
                    "visualization_settings": {},
                },
                "text": intro,
            },
        }
    ]
    row = 5
    managed = set()
    for index, c in enumerate(cards):
        name = "Visa CNC · " + c["name"]
        old = [i for i in items if i["model"] == "card" and i["name"] == name]
        assert len(old) <= 1
        body = {
            "name": name,
            "description": c["description"],
            "display": "table",
            "collection_id": cid,
            "dataset_query": query(c["query"]),
            "visualization_settings": {"table.pivot": False},
        }
        saved = api("PUT", f"card/{old[0]['id']}", body) if old else api("POST", "card", body)
        card_id = saved["id"]
        managed.add(card_id)
        layout.append(
            {
                "id": existing.get(card_id, {}).get("id", -index - 1),
                "card_id": card_id,
                "row": row,
                "col": 0,
                "size_x": 24,
                "size_y": c["height"],
                "parameter_mappings": [
                    {
                        "parameter_id": "visa",
                        "card_id": card_id,
                        "target": ["variable", ["template-tag", "visa"]],
                    }
                ],
                "visualization_settings": {"card.title": c["name"]},
            }
        )
        row += c["height"]
    layout.extend(
        c for c in dash.get("dashcards", []) if c.get("card_id") and c["card_id"] not in managed
    )
    api(
        "PUT",
        f"dashboard/{dash['id']}",
        {
            "name": NAME,
            "description": "Provenance des données courantes par visa CNC, du snapshot source aux modèles finaux. Dernier essai et dernier succès distingués.",
            "parameters": params,
            "dashcards": layout,
        },
    )
    saved = api("GET", f"dashboard/{dash['id']}")
    assert managed.issubset({c.get("card_id") for c in saved["dashcards"]})
    assert all(
        c["parameter_mappings"] for c in saved["dashcards"] if c.get("card_id") in managed
    )
    print(args.url.rstrip("/") + f"/dashboard/{dash['id']}?visa=144246", flush=True)


if __name__ == "__main__":
    main()
