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
        result = self.run_model("staging/stg_allocine_films.sql", {"source_allocine_data": fixture(cols, [old, latest, error, other])})
        self.assertEqual({r["cnc_visa"]: r["allocine_name"] for r in result}, {152722: "Gabin", 152723: "old"})

    def test_tax_credit_encodings(self):
        cols = {name: "text" for name in ["VISA", "TITRE", "GENRE", "ANNEE_D_AGREMENT", "DEVIS", "REALISATEUR", "RANG", "PRODUCTEURS", "PAYANT", "CLAIR", "NATIONALITE", "EOF", "BONUS_PARITE_", "ASR", "SOFICA", "CREDIT_D_IMPOT", "AIDE_REGIONALE", "UPDATED_DATE", "UPDATED_BY", "_airbyte_raw_id"]}
        cols.update(_airbyte_generation_id="integer", _airbyte_extracted_at="timestamp", _airbyte_meta="jsonb")
        values = ["X", " OUI ", "oui", "D", "", None]
        rows = [dict(VISA=str(i+1), CREDIT_D_IMPOT=v, UPDATED_DATE="13/11/2026", UPDATED_BY="Test") for i, v in enumerate(values)]
        result = self.run_model("staging/stg_cnc_films.sql", {"source_films": fixture(cols, rows)})
        self.assertEqual([r["has_tax_credit"] for r in sorted(result, key=lambda r: r["cnc_visa"])], [True, True, True, None, False, False])


if __name__ == "__main__":
    unittest.main()
