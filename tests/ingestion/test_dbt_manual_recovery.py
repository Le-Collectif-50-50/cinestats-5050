"""Régressions SQL PostgreSQL, exécutées uniquement en transaction read-only.

DBT_TEST_SSH et DBT_TEST_DATABASE permettent d'utiliser un serveur PostgreSQL
accessible via SSH (sudo -u postgres). Aucun modèle ni schéma n'est matérialisé.
"""
import json
import os
from pathlib import Path
import subprocess
import unittest

from jinja2 import Environment


MODELS = Path(__file__).resolve().parents[2] / "ingestion/dbt/models"
FILM = "38b226f8-30c1-cf39-0442-5e5560af1579"
PERSON = "7b1345c0-69ed-4b28-341a-acc7e0608afc"
ROLE = "bbd64e7b-0fa4-b6c8-6a65-fd8ae4e76363"


def fixture(columns, rows):
    payload = json.dumps(rows).replace("'", "''")
    fields = ", ".join(f'"{name}" {kind}' for name, kind in columns.items())
    return f"SELECT * FROM jsonb_to_recordset('{payload}'::jsonb) AS t({fields})"


@unittest.skipUnless(os.getenv("DBT_TEST_SSH"), "DBT_TEST_SSH non configuré")
class ManualRecoverySQLTests(unittest.TestCase):
    def run_model(self, path, inputs, sql_template=None):
        env = Environment()
        module = env.from_string(
            (MODELS.parent / "macros/gsheet_updated_timestamp.sql").read_text()
        ).module
        env.globals["gsheet_updated_timestamp"] = module.gsheet_updated_timestamp
        rendered = env.from_string(sql_template or (MODELS / path).read_text()).render(
            ref=lambda name: name,
            source=lambda schema, name: f"source_{name}",
            config=lambda **kwargs: "",
        )
        ctes = ",\n".join(f"{name} AS ({query})" for name, query in inputs.items())
        sql = (
            "BEGIN READ ONLY; SET LOCAL statement_timeout='20s';\n"
            f"WITH {ctes}, result AS ({rendered}) "
            "SELECT COALESCE(json_agg(result), '[]'::json) FROM result; COMMIT;"
        )
        proc = subprocess.run(
            ["ssh", os.environ["DBT_TEST_SSH"], "sudo", "-n", "-u", "postgres",
             "psql", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1",
             "-d", os.environ["DBT_TEST_DATABASE"]],
            input=sql, text=True, capture_output=True, check=True,
        )
        return json.loads(proc.stdout)

    def test_last_name_preserves_remaining_words_in_all_credit_categories(self):
        import hashlib
        import uuid

        cases = [
            ("Eliane de Latour", "de Latour"),
            ("Leonardo Di Caprio", "Di Caprio"),
            ("Jean-Pierre Van der Meersch", "Van der Meersch"),
            ("Lupita Nyong’o", "Nyong’o"),
            ("Élodie Dupont-Martin", "Dupont-Martin"),
            ("Jean Claude Van Damme", "Claude Van Damme"),
            ("Cher", ""),
            ("Eliane   de  Latour", "de Latour"),
            ("Eliane\u00a0de\u202fLatour", "de Latour"),
        ]
        categories = ["direction", "casting", "screenwriters", "production",
                      "technical_team", "distribution", "soundtrack"]
        columns = dict(allocine_id="text", direction="text[]", casting="text[]",
                       **{key: "jsonb" for key in categories[2:]}, companies="jsonb")
        rows = []
        expected = {}
        for category in categories:
            for name, last_name in cases:
                key = str(len(rows))
                value = [name] if category in categories[:2] else [dict(name=name)]
                rows.append(dict(allocine_id=key, **{category: value}))
                expected[key] = (name, last_name)
        result = self.run_model("intermediate/int_credit_holders_role.sql", {
            "stg_allocine_films": fixture(columns, rows),
            "stg_id_matching": fixture(dict(film_id="uuid", allocine_id="text"),
                                       [dict(film_id=FILM, allocine_id=r["allocine_id"]) for r in rows]),
        })
        self.assertEqual(len(result), len(rows))
        for row in result:
            name, last_name = expected[row["allocine_id"]]
            with self.subTest(name=name, allocine_id=row["allocine_id"]):
                self.assertEqual(row["last_name"], last_name)
                self.assertEqual(row["full_name"], name)
                self.assertEqual(row["first_name"], name.split(" ")[0])
                self.assertEqual(row["credit_holder_id"], str(uuid.UUID(hashlib.md5(name.encode()).hexdigest())))
                self.assertEqual(row["film_id"], FILM)

    def test_film_title_matching_priority_and_fallbacks(self):
        cases = [
            (" Dans les yeux de Thomas Pesquet ", "Titre Allociné", "CNC", "Dans les yeux de Thomas Pesquet"),
            ("Correction", None, "CNC", "Correction"),
            (None, " Allociné ", "CNC", "Allociné"),
            ("   ", "Allociné", "CNC", "Allociné"),
            ("", "  ", "CNC", "CNC"),
            (None, None, "CNC", "CNC"),
        ]
        columns = dict(film_id="uuid", cnc_visa="integer", cnc_name="text",
                       cnc_agreement_year="integer", budget="numeric", budget_category="text",
                       broadcasters="text", has_parity_bonus="boolean", has_eof="boolean",
                       has_sofica="boolean", has_tax_credit="boolean",
                       has_regional_funding="boolean", filmography_rank="text", has_asr="boolean")
        for matching, allocine, cnc, expected in cases:
            with self.subTest(matching=matching, allocine=allocine):
                result = self.run_model("fnl/fnl_films.sql", {
                    "int_cnc_films": fixture(columns, [dict(film_id=FILM, cnc_visa=144246, cnc_name=cnc)]),
                    "int_id_matching": fixture(dict(cnc_visa="integer", cnc_name="text"),
                                               [dict(cnc_visa=144246, cnc_name=matching)]),
                    "int_allocine_films": fixture(dict(film_id="uuid", allocine_name="text",
                                                        release_date="date", duration_mn="integer"),
                                                 [dict(film_id=FILM, allocine_name=allocine)]),
                    "fnl_film_country_budget_allocation": fixture(dict(film_id="uuid", country_name="text", budget_allocation="numeric"), []),
                    "fnl_film_genre": fixture(dict(film_id="uuid", genre_id="uuid"), []),
                    "fnl_genre": fixture(dict(genre_id="uuid", genre_name="text"), []),
                })
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["movie_name"], expected)
                self.assertEqual(result[0]["film_id"], FILM)
                self.assertEqual(result[0]["cnc_visa"], 144246)

    def test_aggregated_genres_preserve_manual_associations_and_labels(self):
        documentary = "9ae49857-f08a-c282-64e0-f228627d3e4c"
        drama = "00000000-0000-0000-0000-000000000001"
        manual_only = "00000000-0000-0000-0000-000000000002"
        columns = dict(film_id="uuid", cnc_visa="integer", cnc_name="text",
                       cnc_agreement_year="integer", budget="numeric", budget_category="text",
                       broadcasters="text", has_parity_bonus="boolean", has_eof="boolean",
                       has_sofica="boolean", has_tax_credit="boolean",
                       has_regional_funding="boolean", filmography_rank="text", has_asr="boolean")
        scraped = dict(film_id=FILM, genre_id=drama, genre_name="Drame")
        correction = dict(film_id=FILM, genre_id=documentary)
        cases = [
            ([], [], [], None),
            ([scraped, scraped], [], [], "Drame"),
            ([scraped], [correction, correction],
             [dict(id=documentary, name="Documentaire")], "Documentaire, Drame"),
            ([], [correction], [dict(id=documentary, name="Documentaire")], "Documentaire"),
            ([scraped], [], [dict(id=drama, name="Drame corrigé")], "Drame corrigé"),
            ([scraped], [dict(film_id=FILM, genre_id=drama)], [], "Drame"),
            ([scraped], [dict(film_id=FILM, genre_id=manual_only)],
             [dict(id=manual_only, name="Genre manuel")], "Drame, Genre manuel"),
        ]
        env = Environment()
        for genres, manual, labels, expected in cases:
            with self.subTest(expected=expected, manual=manual):
                inputs = {
                    "int_cnc_films": fixture(columns, [dict(film_id=FILM, cnc_visa=144246, cnc_name="Film")]),
                    "int_id_matching": fixture(dict(cnc_visa="integer", cnc_name="text"),
                                               [dict(cnc_visa=144246, cnc_name="Film")]),
                    "int_allocine_films": fixture(dict(film_id="uuid", allocine_name="text",
                                                        release_date="date", duration_mn="integer"), []),
                    "fnl_film_country_budget_allocation": fixture(
                        dict(film_id="uuid", country_name="text", budget_allocation="numeric"), []),
                    "int_film_genres": fixture(dict(film_id="uuid", genre_id="uuid", genre_name="text"), genres),
                    "int_fix_film_genres": fixture(dict(film_id="uuid", genre_id="uuid"), manual),
                    "int_fix_genres": fixture(dict(id="uuid", name="text"), labels),
                }
                for model in ("fnl_film_genre", "fnl_genre"):
                    inputs[model] = env.from_string((MODELS / "fnl" / f"{model}.sql").read_text()).render(
                        ref=lambda name: name)
                result = self.run_model("fnl/fnl_films.sql", inputs)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["film_id"], FILM)
                self.assertEqual(result[0]["genre"], expected)

    def test_full_name_preserves_corrections_and_manual_people(self):
        cases = [
            # Nom source préservé même si les champs séparés sont incomplets.
            (dict(full_name="Eliane de Latour", first_name="Eliane", last_name="de"),
             dict(gender="female"), "Eliane de Latour"),
            (dict(full_name="Ancien Nom", first_name="Ancien", last_name="Nom"),
             dict(first_name="Eliane", last_name="de Latour"), "Eliane de Latour"),
            (dict(full_name="Eliane de", first_name="Eliane", last_name="de"),
             dict(last_name="de Latour"), "Eliane de Latour"),
            (dict(full_name="Ancien de Latour", first_name="Ancien", last_name="de Latour"),
             dict(first_name="Eliane"), "Eliane de Latour"),
            (None, dict(type="Individual", first_name="Eliane", last_name="de Latour"), "Eliane de Latour"),
            (None, dict(type="Individual", first_name="Cher"), "Cher"),
            (None, dict(type="Individual", last_name="Nyong’o"), "Nyong’o"),
            (dict(full_name="  Jean-Pierre Van der Meersch  "), None, "Jean-Pierre Van der Meersch"),
            (dict(full_name="Élodie Dupont-Martin"), dict(first_name=" ", last_name=""), "Élodie Dupont-Martin"),
            (dict(full_name="Jean\u00a0Claude Van Damme"), None, "Jean\u00a0Claude Van Damme"),
            (dict(first_name="  Lupita ", last_name=" Nyong’o ", full_name=" "), None, "Lupita Nyong’o"),
            (dict(type="Company", legal_name="Société"), None, None),
            (None, dict(type="Company", legal_name="Société"), None),
            (None, dict(type="Individual", gender="female"), None),
        ]
        scraped, corrections, expected = [], [], {}
        for index, (source, fix, name) in enumerate(cases, 1):
            identifier = f"00000000-0000-0000-0000-{index:012d}"
            if source is not None:
                scraped.append(dict({"credit_holder_id": identifier, "type": "Individual", **source}))
            if fix is not None:
                corrections.append(dict(id=identifier, **fix))
            expected[identifier] = name
        result = self.run_model("fnl/fnl_credit_holders.sql", {
            "int_credit_holders_role": fixture(dict(credit_holder_id="uuid", type="text", full_name="text",
                                                      first_name="text", last_name="text", legal_name="text"), scraped),
            "int_credit_holders_genre": fixture(dict(full_name="text", gender="text"), []),
            "int_fix_credit_holders": fixture(dict(id="uuid", type="text", first_name="text", last_name="text",
                                                      legal_name="text", gender="text", birthdate="date"), corrections),
        })
        self.assertEqual(len(result), len(cases))
        self.assertEqual({row["credit_holder_id"]: row["full_name"] for row in result}, expected)
        self.assertTrue(all(row["legal_name"] == "Société" for row in result if row["type"] == "Company"))

    def test_updated_timestamp_formats_and_type(self):
        dates = ["13/11/2026", "13/11/2026 15:42", "13/11/2026 15:42:08",
                 " 1/2/2026 09:05:02 ", "2026-11-13 15:42:08", "", None]
        result = self.run_model(None, {
            "dates": fixture(dict(id="integer", value="text"),
                             [dict(id=i, value=v) for i, v in enumerate(dates)])
        }, sql_template="""
            SELECT id, {{ gsheet_updated_timestamp('value') }} AS parsed,
                   pg_typeof({{ gsheet_updated_timestamp('value') }})::text AS kind
            FROM dates ORDER BY id
        """)
        self.assertEqual([r["parsed"] for r in result], [
            "2026-11-13T00:00:00", "2026-11-13T15:42:00", "2026-11-13T15:42:08",
            "2026-02-01T09:05:02", "2026-11-13T15:42:08", None, None,
        ])
        self.assertTrue(all(r["kind"] == "timestamp without time zone" for r in result))

    def test_updated_timestamp_rejects_invalid_values(self):
        for value in ["31/02/2026 12:00:00", "13/11/2026 25:01:00", "13/11/2026 ignored"]:
            with self.subTest(value=value), self.assertRaises(subprocess.CalledProcessError):
                self.run_model(None, {"dates": fixture(dict(value="text"), [dict(value=value)])},
                               sql_template="SELECT {{ gsheet_updated_timestamp('value') }} FROM dates")

    def test_latest_correction_uses_time_then_airbyte_metadata(self):
        columns = dict(id="uuid", type="text", first_name="text", last_name="text",
                       legal_name="text", gender="text", birthdate="date", updated_date="timestamp",
                       airbyte_extraction_date="timestamp", airbyte_raw_id="text")
        base = dict(id=PERSON, type="Individual", first_name="Maxence", last_name="Voiseux")
        rows = [dict(base, gender="old", updated_date="2026-11-13 15:42:07"),
                dict(base, gender="male", updated_date="2026-11-13 15:42:08",
                     airbyte_extraction_date="2026-11-13 16:00:00", airbyte_raw_id="b"),
                dict(base, gender="old_tie", updated_date="2026-11-13 15:42:08",
                     airbyte_extraction_date="2026-11-13 15:59:00", airbyte_raw_id="z"),
                dict(base, gender="null_date", updated_date=None)]
        for ordered in (rows, list(reversed(rows))):
            result = self.run_model("intermediate/int_fix_credit_holders.sql", {
                "stg_fix_credit_holders": fixture(columns, ordered),
            })
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["gender"], "male")

    def test_manual_credit_added_and_duplicate_removed(self):
        cols = dict(film_id="uuid", role_id="uuid", credit_holder_id="uuid")
        row = dict(film_id=FILM, role_id=ROLE, credit_holder_id=PERSON)
        for scraped in ([], [row, row]):
            result = self.run_model("fnl/fnl_film_credits.sql", {
                "int_credit_holders_role": fixture(cols, scraped),
                "int_fix_film_credits": fixture(cols, [row]),
            })
            self.assertEqual(result, [row])

    def test_manual_film_genres_added_without_replacing_scraped_associations(self):
        columns = dict(film_id="uuid", genre_id="uuid")
        documentary = "9ae49857-f08a-c282-64e0-f228627d3e4c"
        drama = "00000000-0000-0000-0000-000000000001"
        other_film = "00000000-0000-0000-0000-000000000002"
        manual = dict(film_id=FILM, genre_id=documentary)
        existing = dict(film_id=FILM, genre_id=drama)
        unrelated = dict(film_id=other_film, genre_id=drama)
        cases = [
            ([], [manual], [manual]),
            ([existing, unrelated], [manual], [existing, unrelated, manual]),
            ([manual, manual, existing], [manual, manual], [manual, existing]),
            ([existing, unrelated], [], [existing, unrelated]),
            ([], [], []),
        ]
        for scraped, corrections, expected in cases:
            with self.subTest(scraped=scraped, corrections=corrections):
                result = self.run_model("fnl/fnl_film_genre.sql", {
                    "int_film_genres": fixture(columns, scraped),
                    "int_fix_film_genres": fixture(columns, corrections),
                })
                self.assertCountEqual(result, expected)

    def test_manual_person_added_and_overrides_existing(self):
        cols = dict(credit_holder_id="uuid", type="text", first_name="text",
                    last_name="text", legal_name="text", full_name="text")
        fixcols = dict(id="uuid", type="text", first_name="text", last_name="text",
                       legal_name="text", gender="text", birthdate="date")
        fix = dict(id=PERSON, type="Individual", first_name="Maxence", last_name="Voiseux", gender="male")
        for scraped in ([], [dict(credit_holder_id=PERSON, type="Individual", first_name="Wrong", full_name="Maxence Voiseux")]):
            result = self.run_model("fnl/fnl_credit_holders.sql", {
                "int_credit_holders_role": fixture(cols, scraped),
                "int_credit_holders_genre": fixture(dict(full_name="text", gender="text"), []),
                "int_fix_credit_holders": fixture(fixcols, [fix]),
            })
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["credit_holder_id"], PERSON)
            self.assertEqual(result[0]["first_name"], "Maxence")
            self.assertEqual(result[0]["gender"], "male")

    def test_hugo_correction_accepted_and_person_example_excluded(self):
        cols = {name: "text" for name in ["CREDIT_HOLDER_ID", "TYPE", "FIRST_NAME", "LAST_NAME", "LEGAL_NAME", "GENDER", "BIRTHDATE", "UPDATED_DATE", "UPDATED_BY", "_airbyte_raw_id"]}
        cols.update(_airbyte_generation_id="integer", _airbyte_extracted_at="timestamp", _airbyte_meta="jsonb")
        row = dict(CREDIT_HOLDER_ID=PERSON, FIRST_NAME="Maxence", LAST_NAME="Voiseux", BIRTHDATE="", LEGAL_NAME=" ", UPDATED_DATE="13/11/2026", UPDATED_BY="Hugo Laurens")
        example = dict(row, CREDIT_HOLDER_ID="000a676c-8ef7-5b14-8a67-9431ceeb933e", FIRST_NAME="Example", LAST_NAME="Example")
        result = self.run_model("staging/stg_fix_credit_holders.sql", {"source_credit_holders": fixture(cols, [row, example])})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], PERSON)
        self.assertIsNone(result[0]["legal_name"])
        self.assertIsNone(result[0]["birthdate"])

    def test_hugo_credit_accepted_and_exact_example_excluded(self):
        cols = {name: "text" for name in ["FILM_ID", "ROLE_ID", "CREDIT_HOLDER_ID", "UPDATED_DATE", "UPDATED_BY", "_airbyte_raw_id"]}
        cols.update(_airbyte_generation_id="integer", _airbyte_extracted_at="timestamp", _airbyte_meta="jsonb")
        row = dict(FILM_ID=FILM, ROLE_ID=ROLE, CREDIT_HOLDER_ID=PERSON, UPDATED_DATE="13/11/2026", UPDATED_BY="Hugo Laurens")
        example = dict(row, FILM_ID="0016b072-7ad8-f224-cfd7-053b56ff2720", ROLE_ID="d894803c-210d-2b5b-6e7e-50f2d418bfcf", CREDIT_HOLDER_ID="d8f8d53c-51b8-f89b-1a8d-da48da142694", UPDATED_DATE="25/04/2026")
        result = self.run_model("staging/stg_fix_film_credits.sql", {"source_film_credits": fixture(cols, [row, example])})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["film_id"], FILM)

    def test_latest_success_per_visa_not_latest_error_or_shared_allocine_id(self):
        cols = {name: "text" for name in ["visa_number", "allocine_visa_number", "allocine_id", "original_name", "allocine_title", "cnc_agrement_year", "release_date_raw", "release_date", "duration_raw", "duration_minutes", "search_url", "source_url", "allocine_url", "poster_url", "trailer_url", "run_id", "source_record_id", "match_strategy", "scrape_status", "error_message", "record_hash"]}
        cols.update(extracted_at="timestamp")
        cols.update({name: "jsonb" for name in ["genres", "direction", "casting", "screenwriters", "production", "technical_team", "soundtrack", "distribution", "companies"]})
        old = dict(visa_number="152722", source_record_id="152722", allocine_id="298873", allocine_title="old", extracted_at="2026-11-11", scrape_status="success")
        latest = dict(old, allocine_title="Gabin", extracted_at="2026-11-12")
        error = dict(old, extracted_at="2026-11-13", scrape_status="error")
        other = dict(old, visa_number="152723", source_record_id="152723")
        rejection_cols = dict(source_record_id="text", visa_number="text", allocine_id="text")
        inputs = {
            "source_allocine_data": fixture(cols, [old, latest, error, other]),
            "allocine_association_rejections": fixture(rejection_cols, []),
        }
        result = self.run_model("staging/stg_allocine_films.sql", inputs)
        self.assertEqual({r["cnc_visa"]: r["allocine_name"] for r in result}, {152722: "Gabin", 152723: "old"})

        # Le rejet couvre tous les succès de l'association et les recollectes.
        # Le même ID d'un autre visa reste exploitable.
        review = dict(old, extracted_at="2026-11-14", scrape_status="needs_review",
                      allocine_id="999999")
        inputs["source_allocine_data"] = fixture(cols, [old, latest, error, other, review])
        inputs["allocine_association_rejections"] = fixture(rejection_cols, [
            dict(source_record_id="152722", visa_number="152722", allocine_id="298873")
        ])
        result = self.run_model("staging/stg_allocine_films.sql", inputs)
        self.assertEqual([(r["cnc_visa"], r["allocine_name"]) for r in result], [(152723, "old")])

        # Une nouvelle cible confirmée peut remplacer l'association rejetée.
        replacement = dict(review, scrape_status="success", allocine_title="Correct")
        inputs["source_allocine_data"] = fixture(cols, [old, latest, other, review, replacement])
        result = self.run_model("staging/stg_allocine_films.sql", inputs)
        self.assertEqual({r["cnc_visa"]: r["allocine_id"] for r in result},
                         {152722: "999999", 152723: "298873"})


    def test_rejected_archive_uses_latest_success_and_company_namespace(self):
        import hashlib
        import uuid

        cols = dict(visa_number="text", source_record_id="text", allocine_id="text",
                    run_id="text", record_hash="text", extracted_at="timestamp",
                    scrape_status="text")
        cols.update({name: "jsonb" for name in ["direction", "casting", "screenwriters",
                     "production", "technical_team", "distribution", "soundtrack", "companies"]})
        old = dict(visa_number="120846", source_record_id="120846", allocine_id="109311",
                   run_id="old", record_hash="a", extracted_at="2026-11-12",
                   scrape_status="success", direction=["Old director"])
        latest = dict(old, run_id="latest", extracted_at="2026-11-13",
                      direction=["Clive Gordon"],
                      companies=[dict(name="Company", role="Production")])
        failure = dict(latest, run_id="error", extracted_at="2026-11-14", scrape_status="error")
        result = self.run_model("ops/allocine_rejected_credits.sql", {
            "allocine_rejected_results": fixture(cols, [old, latest, failure])
        })
        self.assertEqual(len(result), 2)
        self.assertEqual({r["run_id"] for r in result}, {"latest"})
        company = next(r for r in result if r["type"] == "Company")
        expected = str(uuid.UUID(hashlib.md5(b"company:Company").hexdigest()))
        self.assertEqual(company["credit_holder_id"], expected)
        self.assertEqual({r["source_visa"] for r in result}, {"120846"})

    def test_exact_euro_budgets_and_categories_across_agreement_years(self):
        cols = {name: "text" for name in ["VISA", "TITRE", "GENRE", "ANNEE_D_AGREMENT", "DEVIS", "REALISATEUR", "RANG", "PRODUCTEURS", "PAYANT", "CLAIR", "NATIONALITE", "EOF", "BONUS_PARITE_", "ASR", "SOFICA", "CREDIT_D_IMPOT", "AIDE_REGIONALE", "UPDATED_DATE", "UPDATED_BY", "_airbyte_raw_id"]}
        cols.update(_airbyte_generation_id="integer", _airbyte_extracted_at="timestamp", _airbyte_meta="jsonb")
        cases = [
            (2012, "3 785 000", "3785000", "2 à 5M€"),
            (2013, "3\u00a0785\u00a0000", "3785000", "2 à 5M€"),
            (2024, "3\u202f785\u202f000,12", "3785000.12", "2 à 5M€"),
            (None, "3785000.12", "3785000.12", "2 à 5M€"),
            (2017, "4996371", "4996371", "2 à 5M€"),
            (2018, "4995717", "4995717", "2 à 5M€"),
            (2023, "4998106", "4998106", "2 à 5M€"),
            (2024, "1999999,99", "1999999.99", "Moins de 2M€"),
            (2024, "2000000", "2000000", "2 à 5M€"),
            (2024, "5000000", "5000000", "5 à 10M€"),
            (2024, "10000000", "10000000", "10 à 20M€"),
            (2024, "20000000", "20000000", "Plus de 20M€"),
            (2024, "", None, None),
            (2024, " \u00a0\u202f", None, None),
            (2024, None, None, None),
            (2024, "0", "0", "Moins de 2M€"),
        ]
        rows = [dict(VISA=str(i + 1), ANNEE_D_AGREMENT=year, DEVIS=raw,
                     UPDATED_DATE="15/11/2026", UPDATED_BY="Test")
                for i, (year, raw, _, _) in enumerate(cases)]
        staging = self.run_model("staging/stg_cnc_films.sql", {
            "source_films": fixture(cols, rows),
        }, sql_template=(
            "SELECT cnc_visa, budget::text AS amount, pg_typeof(budget)::text AS kind "
            "FROM (" + (MODELS / "staging/stg_cnc_films.sql").read_text() + ") AS films"
        ))
        self.assertEqual(len(staging), len(cases))
        self.assertEqual([r["amount"] for r in sorted(staging, key=lambda r: r["cnc_visa"])],
                         [expected for _, _, expected, _ in cases])
        self.assertEqual({r["kind"] for r in staging}, {"numeric"})
        # Exécuter les deux vrais modèles ensemble, y compris leurs seuils métier.
        env = Environment()
        env.globals["gsheet_updated_timestamp"] = env.from_string(
            (MODELS.parent / "macros/gsheet_updated_timestamp.sql").read_text()
        ).module.gsheet_updated_timestamp
        stage_sql = env.from_string((MODELS / "staging/stg_cnc_films.sql").read_text()).render(
            source=lambda schema, name: "source_films", config=lambda **kwargs: "")
        categories = self.run_model("intermediate/int_cnc_films.sql", {
            "source_films": fixture(cols, rows),
            "stg_cnc_films": stage_sql,
            "stg_id_matching": fixture(dict(film_id="uuid", cnc_visa="integer"), []),
        })
        self.assertEqual(len(categories), len(cases))
        self.assertEqual([r["budget_category"] for r in sorted(categories, key=lambda r: r["cnc_visa"])],
                         [category for _, _, _, category in cases])

    def test_tax_credit_encodings(self):
        cols = {name: "text" for name in ["VISA", "TITRE", "GENRE", "ANNEE_D_AGREMENT", "DEVIS", "REALISATEUR", "RANG", "PRODUCTEURS", "PAYANT", "CLAIR", "NATIONALITE", "EOF", "BONUS_PARITE_", "ASR", "SOFICA", "CREDIT_D_IMPOT", "AIDE_REGIONALE", "UPDATED_DATE", "UPDATED_BY", "_airbyte_raw_id"]}
        cols.update(_airbyte_generation_id="integer", _airbyte_extracted_at="timestamp", _airbyte_meta="jsonb")
        values = ["X", " OUI ", "oui", "D", "", None]
        rows = [dict(VISA=str(i+1), CREDIT_D_IMPOT=v, UPDATED_DATE="13/11/2026", UPDATED_BY="Test") for i, v in enumerate(values)]
        result = self.run_model("staging/stg_cnc_films.sql", {"source_films": fixture(cols, rows)})
        self.assertEqual([r["has_tax_credit"] for r in sorted(result, key=lambda r: r["cnc_visa"])], [True, True, True, None, False, False])


if __name__ == "__main__":
    unittest.main()
