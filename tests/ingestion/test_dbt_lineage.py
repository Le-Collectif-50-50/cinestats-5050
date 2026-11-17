"""Vérifier les dépendances documentées et la stabilité du rendu GitHub."""

import importlib.util
from pathlib import Path
import re
import unittest


SPEC = importlib.util.spec_from_file_location(
    "dbt_lineage", Path(__file__).resolve().parents[2] / "scripts/generate_dbt_lineage.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def resource(name, kind, schema, parents=()):
    return {
        "name": name, "resource_type": kind, "schema": schema,
        "package_name": "ric", "original_file_path": f"models/{name}.sql",
        "depends_on": {"nodes": list(parents)}, "config": {},
    }


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "metadata": {"project_name": "ric"},
            "sources": {"source.ric.raw.films": resource("films", "source", "raw")},
            "nodes": {
                "model.ric.stage": resource("stage", "model", "staging", ["source.ric.raw.films"]),
                "model.ric.final": resource("final", "model", "fnl", ["model.ric.stage"]),
                "test.ric.check": resource("check", "test", "fnl", ["model.ric.final"]),
                "seed.ric.seed": resource("seed", "seed", "raw"),
                "snapshot.ric.history": resource("history", "snapshot", "history", ["model.ric.final"]),
            },
        }

    def render(self):
        return MODULE.render(self.manifest, "https://github.com/org/repo/tree/abc", "2026-11-14")

    def test_graph_uses_declared_edges_and_excludes_tests(self):
        result = self.render()
        self.assertIn("1 sources, 2 modèles, 1 seeds, 1 snapshots ; 3 dépendances directes", result)
        self.assertEqual(result.count(" --> "), 6)
        self.assertNotIn("fnl.check", result)
        self.assertIn("/tree/abc/ingestion/dbt/models/final.sql", result)
        self.assertIn('(["raw.films"])', result)

    def test_complete_graph_preserves_cross_schema_chain_and_isolated_seed(self):
        result = self.render()
        graph = result.split("```mermaid\n", 1)[1].split("```", 1)[0]
        self.assertEqual(graph.count(" --> "), 3)
        # Les identifiants sont retrouvés par libellé, sans dépendre du tri interne.
        ids = {label: key for key, label in re.findall(r'(n\d+)\[?\(?\["([^"]+)"', graph)}
        for parent, child in [("raw.films", "staging.stage"), ("staging.stage", "fnl.final"), ("fnl.final", "history.history")]:
            self.assertIn(f"{ids[parent]} --> {ids[child]}", graph)
        self.assertIn("raw.seed", ids)
        self.assertEqual(len(ids), 5)
        self.assertLess(result.index("## Lineage dbt complet"), result.index("<details>"))

    def test_order_is_deterministic(self):
        before = self.render()
        self.manifest["nodes"] = dict(reversed(list(self.manifest["nodes"].items())))
        self.assertEqual(before, self.render())

    def test_missing_parent_fails_instead_of_silently_dropping_edge(self):
        del self.manifest["sources"]["source.ric.raw.films"]
        with self.assertRaisesRegex(ValueError, "Dépendance absente"):
            self.render()

    def test_disabled_resources_are_excluded(self):
        self.manifest["nodes"]["seed.ric.seed"]["config"]["enabled"] = False
        self.assertNotIn("raw.seed", self.render())

    def test_aliases_and_special_characters(self):
        self.manifest["nodes"]["model.ric.final"]["alias"] = 'film|"<titre>'
        result = self.render()
        self.assertIn("fnl.film&#124;&quot;&lt;titre&gt;", result)
        self.assertNotIn('fnl.film|"<titre>', result)

    def test_empty_manifest_fails(self):
        self.manifest["sources"] = {}
        self.manifest["nodes"] = {}
        with self.assertRaisesRegex(ValueError, "aucune ressource"):
            self.render()


if __name__ == "__main__":
    unittest.main()
