"""Contrats du déclenchement Allociné depuis Metabase, sans accès réseau."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from ingestion.prefect import flows


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("metabase_review", ROOT / "infra/data/metabase-scraping-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(
            main_deployment_name="main/deployment", flow_run_name_prefix="metabase-ingestion",
            run_airbyte_sync_step=True, run_dbt_phase_2_step=True, airbyte_connection_names=["Sheets"],
        )
        self.row = {"request_id": uuid4(), "request_source": "metabase",
                    "requested_by_metabase_user": "Test", "request_type": "allocine", "max_films": 27}
        self.client = AsyncMock()
        self.client.read_deployment_by_name.return_value = SimpleNamespace(id=uuid4())
        self.client.create_flow_run_from_deployment.return_value = SimpleNamespace(id=uuid4())

    def dispatch(self):
        context = AsyncMock()
        context.__aenter__.return_value = self.client
        with patch.object(flows, "get_client", return_value=context):
            return asyncio.run(flows._trigger_ingestion_request_run(self.settings, request_row=self.row))

    def test_allocine_routes_limit_and_request_without_ingestion_parameters(self):
        result = self.dispatch()
        self.client.read_deployment_by_name.assert_awaited_once_with(flows.ALLOCINE_DEPLOYMENT_NAME)
        kwargs = self.client.create_flow_run_from_deployment.call_args.kwargs
        self.assertEqual(kwargs["parameters"], {"max_films": 27, "request_id": str(self.row["request_id"])})
        self.assertEqual(kwargs["idempotency_key"], str(self.row["request_id"]))
        self.assertEqual(result, str(self.client.create_flow_run_from_deployment.return_value.id))

    def test_old_ingestion_requests_keep_their_parameters(self):
        del self.row["request_type"]
        self.dispatch()
        self.client.read_deployment_by_name.assert_awaited_once_with("main/deployment")
        parameters = self.client.create_flow_run_from_deployment.call_args.kwargs["parameters"]
        self.assertTrue(parameters["run_airbyte_sync_step"])
        self.assertNotIn("max_films", parameters)

    def test_invalid_limit_or_type_never_reaches_prefect(self):
        for invalid in (None, 0, -1, 2.5, True, "10"):
            self.row["max_films"] = invalid
            with self.assertRaises(ValueError):
                self.dispatch()
        self.row["request_type"] = "unknown"
        with self.assertRaises(ValueError):
            self.dispatch()
        self.client.create_flow_run_from_deployment.assert_not_called()


class LifecycleTests(unittest.TestCase):
    def test_prefect_cancellation_releases_the_request(self):
        request_id, run_id = uuid4(), uuid4()
        connection = Mock()
        connection.execute.return_value.fetchall.return_value = [
            {"request_id": request_id, "triggered_flow_run_id": str(run_id)}]
        db_context = Mock()
        db_context.__enter__ = Mock(return_value=connection)
        db_context.__exit__ = Mock(return_value=False)
        client = AsyncMock()
        from prefect.states import Cancelled
        client.read_flow_run.return_value = SimpleNamespace(state=Cancelled(message="Arrêt demandé"))
        api_context = AsyncMock()
        api_context.__aenter__.return_value = client
        with patch.object(flows, "_connect_request_db", return_value=db_context), \
                patch.object(flows, "get_client", return_value=api_context), \
                patch.object(flows, "_mark_request_failed") as failed:
            asyncio.run(flows._reconcile_allocine_requests("settings"))
        failed.assert_called_once_with("settings", request_id=request_id,
                                       error_message="Prefect Cancelled: Arrêt demandé")

    def test_success_and_failure_are_written_after_scraping(self):
        request_id = uuid4()
        for exception in (None, RuntimeError("browser unavailable")):
            calls = Mock()
            calls.scrape.side_effect = exception
            with patch.object(flows.IngestionRequestSettings, "from_env", return_value="settings"), \
                    patch.object(flows, "_mark_request_processing", calls.processing), \
                    patch.object(flows, "_run_allocine_scraping_step", calls.scrape), \
                    patch.object(flows, "_mark_request_success", calls.success), \
                    patch.object(flows, "_mark_request_failed", calls.failed):
                if exception:
                    with self.assertRaisesRegex(RuntimeError, "browser unavailable"):
                        flows.run_allocine_scraping.fn(max_films=27, request_id=str(request_id))
                else:
                    flows.run_allocine_scraping.fn(max_films=27, request_id=str(request_id))
            self.assertEqual([c[0] for c in calls.mock_calls],
                             ["processing", "scrape", "failed" if exception else "success"])
            calls.scrape.assert_called_once_with(config_path=str(flows.ALLOCINE_CONFIG_PATH), max_films=27)


class DashboardTests(unittest.TestCase):
    def test_requests_do_not_inherit_film_filters(self):
        cards = {card["name"]: card for card in review.dashboard_cards()}
        requests = review.dataset_query(3, cards["Demandes de scraping Allociné"]["query"])
        self.assertEqual(requests["native"]["template-tags"], {})
        chart = cards["Statuts des films par heure"]
        tags = review.dataset_query(3, chart["query"], 123)["native"]["template-tags"]
        self.assertEqual(set(tags), {"visa", "titre", "periode"})
        self.assertEqual(tags["periode"]["dimension"], ["field", 123, None])
        self.assertEqual(chart["visualization_settings"]["stackable.stack_type"], "stacked")
        self.assertNotIn("review_queue", chart["query"])

    def test_action_requires_identity_reason_and_positive_integer_limit(self):
        body = review.action_body(3, 38)
        tags = body["dataset_query"]["native"]["template-tags"]
        self.assertEqual(set(tags), {"email", "reason", "max_films"})
        self.assertTrue(all(tag["required"] for tag in tags.values()))
        self.assertEqual(tags["max_films"]["default"], 10)
        self.assertEqual(review.action_placement(9, -10)["parameter_mappings"], [])


if __name__ == "__main__":
    unittest.main()
