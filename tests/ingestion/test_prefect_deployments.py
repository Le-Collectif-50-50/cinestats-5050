"""Contrats des cinq déploiements, sans API, scraping ni écriture en base."""
import importlib
import asyncio
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ingestion.prefect import flows


ROOT = Path(__file__).resolve().parents[2]
WORKER_SCRIPT = (ROOT / "ingestion/prefect/start_worker.sh").read_text()


class DeploymentTests(unittest.TestCase):
    def test_ingestion_never_calls_scrapers(self):
        calls = Mock()
        with patch.object(flows, "get_run_logger"), \
                patch.object(flows, "_run_airbyte_sync_step", calls.airbyte), \
                patch.object(flows, "_run_dbt_phase_1_step", calls.phase1), \
                patch.object(flows, "_run_dbt_phase_2_step", calls.phase2), \
                patch.object(flows, "_run_allocine_scraping_step") as allocine, \
                patch.object(flows, "_run_mubi_cnc_scraping_step") as mubi:
            flows.main_ingestion_flow.fn()
        self.assertEqual([c[0] for c in calls.mock_calls], ["airbyte", "phase1", "phase2"])
        allocine.assert_not_called()
        mubi.assert_not_called()

    def test_existing_env_migrates_to_new_deployment(self):
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "unused", "POSTGRES_DB": "unused",
            "INGESTION_REQUEST_POSTGRES_PASSWORD": "unused",
            "INGESTION_REQUEST_AIRBYTE_CONNECTION_NAMES": "Sheets",
            "INGESTION_REQUEST_MAIN_DEPLOYMENT_NAME": flows.LEGACY_MAIN_DEPLOYMENT_NAME,
        }, clear=True):
            settings = flows.IngestionRequestSettings.from_env()
        self.assertEqual(settings.main_deployment_name, flows.DEFAULT_MAIN_DEPLOYMENT_NAME)
        self.assertNotIn("config_path", flows._build_request_parameters(settings, request_id=flows.UUID(int=1)))

    def test_scraper_flow_limits_and_schema(self):
        for flow in (flows.run_allocine_scraping, flows.run_mubi_cnc_scraping):
            self.assertEqual(flow.parameters.properties["max_films"]["default"], 10)
            self.assertEqual(flow.parameters.properties["max_films"]["exclusiveMinimum"], 0)
            for kwargs, expected in [({}, "10"), ({"max_films": 25}, "25")]:
                with patch.object(flows, "get_run_logger"), patch.object(flows, "_run_airbyte_sync_step"), patch.object(flows, "_run_dbt_phase_2_step"), patch.object(flows, "_run") as run, patch.object(flows, "_run_mubi_cnc_scraping_step") as mubi:
                    flow.fn(**kwargs)
                    if flow is flows.run_mubi_cnc_scraping:
                        self.assertEqual(mubi.call_args.kwargs["max_films"], int(expected))
                    else:
                        self.assertEqual(run.call_args.args[0][-2:], ["--limit", expected])
            for invalid in (0, -1, True, 1.5):
                with patch.object(flows, "_run") as run, self.assertRaises(ValueError):
                    flow.fn(max_films=invalid)
                run.assert_not_called()

    def test_cli_limits_override_config_without_rewriting_it(self):
        for package, class_name, result in [
            ("allocine", "AllocineAirbyteSource", 0),
            ("mubi_cnc", "MubiCncAirbyteSource", {}),
        ]:
            cli = importlib.import_module(f"ingestion.scraping.{package}.main")
            connector = importlib.import_module(f"ingestion.scraping.{package}.connector")
            with patch.object(cli, "_load_dotenv"), \
                    patch.object(cli, "_load_json", return_value={"scrape_limit": 999}), \
                    patch.object(connector, class_name) as source, \
                    patch("sys.argv", ["scraper", "sync", "--limit", "7"]):
                source.return_value.sync_to_postgres.return_value = result
                self.assertEqual(cli.main(), 0)
                self.assertEqual(source.return_value.sync_to_postgres.call_args.args[0]["scrape_limit"], 7)
            for value in ("0", "-1"):
                with patch.object(cli, "_load_dotenv"), \
                        patch("sys.argv", ["scraper", "sync", "--limit", value]), \
                        patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                    cli.main()

    def test_startup_registers_exactly_five_deployments_without_scraping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / "prefect"
            fake.write_text(
                "#!/usr/bin/env python3\nimport json, os, sys\n"
                "with open(os.environ['PREFECT_TEST_LOG'], 'a') as f: "
                "f.write(json.dumps(sys.argv[1:])+'\\n')\n"
            )
            fake.chmod(0o700)
            log = root / "calls"
            env = dict(os.environ, PATH=f"{directory}:{os.environ['PATH']}", PREFECT_TEST_LOG=str(log))
            script = WORKER_SCRIPT.replace("/tmp/prefect-", f"{directory}/prefect-")
            subprocess.run(["bash", "-s"], input=script, text=True, env=env, check=True)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
        deployments = [c for c in calls if "deploy" in c]
        names = {c[c.index("--name") + 1]: c for c in deployments}
        self.assertEqual(set(names), {
            "lancer-ingestion-complete", "lancer-scrapping-allocine",
            "lancer-scrapping-mubi", "traiter-les-demandes-ingestion",
            "rechercher-identifiants-manquants",
        })
        for name, args in names.items():
            self.assertEqual("--interval" in args, name == "traiter-les-demandes-ingestion")
            self.assertNotIn("--cron", args)
        self.assertFalse(any(c[:2] == ["deployment", "run"] for c in calls))
        deleted = {c[2] for c in calls if c[:2] == ["deployment", "delete"]}
        self.assertIn(flows.LEGACY_MAIN_DEPLOYMENT_NAME, deleted)
        self.assertIn("Recuperer les donnees Allocine/lancer-scrapping-allocine", deleted)
        self.assertIn("Recuperer les donnees Mubi (CNC)/lancer-scrapping-mubi", deleted)
        self.assertNotIn("Rechercher les identifiants MUBI et TMDB/rechercher-identifiants-manquants", deleted)
        self.assertEqual(names["rechercher-identifiants-manquants"][names["rechercher-identifiants-manquants"].index("--concurrency-limit") + 1], "1")

    def test_id_matching_is_separate_and_passes_target_parameters(self):
        with patch.object(flows, "_run") as run, \
                patch.object(flows, "_run_airbyte_sync_step") as airbyte, \
                patch.object(flows, "_run_dbt_phase_2_step") as dbt:
            flows.run_missing_id_matching.fn(provider="tmdb", max_films=3,
                                            visa_number="149572", max_candidates=20, dry_run=True)
        self.assertEqual(run.call_args.args[0], [
            "python3", "-u", "-m", "ingestion.scraping.id_matching", "--provider", "tmdb",
            "--limit", "3", "--max-candidates", "20", "--visa", "149572", "--dry-run",
        ])
        airbyte.assert_not_called()
        dbt.assert_not_called()
        parameters = flows.run_missing_id_matching.parameters.properties
        self.assertEqual(parameters["max_films"]["exclusiveMinimum"], 0)
        self.assertEqual(parameters["max_candidates"]["exclusiveMinimum"], 0)

    def test_id_matching_rejects_invalid_parameters_before_subprocess(self):
        for kwargs in ({"max_films": 0}, {"provider": "imdb"}, {"visa_number": "0"},
                       {"max_candidates": True}, {"max_candidates": -1}, {"dry_run": "false"}):
            with self.subTest(kwargs=kwargs), patch.object(flows, "_run") as run:
                with self.assertRaises(ValueError):
                    flows.run_missing_id_matching.fn(**kwargs)
                run.assert_not_called()

    def test_id_matching_propagates_failure_to_prefect(self):
        with patch.object(flows, "_run", side_effect=subprocess.CalledProcessError(1, ["matching"])):
            with self.assertRaises(subprocess.CalledProcessError):
                flows.run_missing_id_matching.fn()

    def test_id_matching_backfill_keeps_explicit_batch_targets(self):
        with patch.object(flows, "_run") as run:
            flows.run_missing_id_matching.fn(visa_numbers=["149572", "88240"], skip_processed=True)
        self.assertEqual(run.call_args.args[0][-4:], ["--visas", "149572", "88240", "--skip-processed"])
        for kwargs in ({"visa_numbers": []}, {"visa_numbers": ["0"]},
                       {"visa_numbers": ["149572", "149572"]},
                       {"visa_number": "149572", "visa_numbers": ["88240"]},
                       {"max_films": 1, "visa_numbers": ["149572", "88240"]}):
            with self.subTest(kwargs=kwargs), patch.object(flows, "_run") as run:
                with self.assertRaises(ValueError):
                    flows.run_missing_id_matching.fn(**kwargs)
                run.assert_not_called()

    def test_id_matching_waits_for_predecessor_before_launch(self):
        key = str(flows.UUID(int=1))
        with patch.object(flows, "_wait_for_matching_predecessor", new_callable=AsyncMock) as wait, \
                patch.object(flows, "_run") as run:
            flows.run_missing_id_matching.fn(wait_for_flow_run_id=key)
        wait.assert_awaited_once_with(key)
        run.assert_called_once()

    def test_predecessor_wait_stops_after_terminal_state(self):
        client = AsyncMock()
        pending, finished = Mock(), Mock()
        pending.state.is_final.return_value = False
        finished.state.is_final.return_value = True
        client.read_flow_run.side_effect = [pending, finished]
        context = AsyncMock()
        context.__aenter__.return_value = client
        with patch.object(flows, "get_client", return_value=context), \
                patch.object(flows, "get_run_logger"), \
                patch.object(flows.asyncio, "sleep", new_callable=AsyncMock) as sleep:
            asyncio.run(flows._wait_for_matching_predecessor(str(flows.UUID(int=1))))
        self.assertEqual(client.read_flow_run.await_count, 2)
        sleep.assert_awaited_once_with(30)


if __name__ == "__main__":
    unittest.main()
