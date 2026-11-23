"""Exécuter les régressions du mapping sur PostgreSQL, sans matérialisation.

DBT_TEST_SSH / DBT_TEST_DATABASE : accès SSH au serveur de test.
Le seed local est injecté en CTE et toutes les requêtes sont en lecture seule.
"""
import csv
import json
import os
from pathlib import Path
import subprocess
import unittest

from jinja2 import Environment


PROJECT = Path(__file__).resolve().parents[2] / "ingestion/dbt"


def render_environment():
    env = Environment()
    env.globals["ref"] = lambda name: name
    env.globals["config"] = lambda **kwargs: ""
    module = env.from_string(
        (PROJECT / "macros/cnc_broadcaster_tokens.sql").read_text()
    ).module
    env.globals["cnc_broadcaster_tokens"] = module.cnc_broadcaster_tokens
    return env


def seed_cte():
    with (PROJECT / "seeds/cnc_broadcaster_aliases.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["priority"] = int(row["priority"])
        row["is_excluded"] = row["is_excluded"] == "true"
    payload = json.dumps(rows, ensure_ascii=False).replace("'", "''")
    return (
        "cnc_broadcaster_aliases AS (SELECT * FROM jsonb_to_recordset("
        f"'{payload}'::jsonb) AS t(priority integer, alias_pattern text, "
        "broadcaster_name text, is_excluded boolean))"
    )


@unittest.skipUnless(os.getenv("DBT_TEST_SSH"), "DBT_TEST_SSH non configuré")
class BroadcasterSQLTests(unittest.TestCase):
    def test_normalization_on_postgresql(self):
        query = render_environment().from_string(
            (PROJECT / "tests/cnc_broadcasters_normalization.sql").read_text()
        ).render()
        sql = (
            "BEGIN READ ONLY; SET LOCAL statement_timeout='20s'; "
            f"WITH {seed_cte()}, failures AS ({query}) "
            "SELECT COALESCE(json_agg(failures), '[]'::json) FROM failures; COMMIT;"
        )
        result = subprocess.run(
            ["ssh", os.environ["DBT_TEST_SSH"], "sudo", "-n", "-u", "postgres",
             "psql", "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1",
             "-d", os.environ["DBT_TEST_DATABASE"]],
            input=sql, text=True, capture_output=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout), [])
