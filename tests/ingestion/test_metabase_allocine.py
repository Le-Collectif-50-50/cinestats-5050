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

    def test_target_routes_visa_force_and_airbyte_connections(self):
        self.row.update(visa_number="144246", force_rescrape=True, max_films=1)
        self.dispatch()
        parameters = self.client.create_flow_run_from_deployment.call_args.kwargs["parameters"]
        self.assertEqual(parameters, {"request_id": str(self.row["request_id"]), "max_films": 1,
                                     "visa_number": "144246", "force_rescrape": True,
                                     "airbyte_connection_names": ["Sheets"]})

    def test_target_rejects_invalid_visa_force_or_limit_before_dispatch(self):
        for values in ({"force_rescrape": True}, {"visa_number": "1;SELECT"},
                       {"visa_number": "000"}, {"visa_number": 144246},
                       {"visa_number": "144246", "force_rescrape": "false"},
                       {"visa_number": "144246", "max_films": 2}):
            with self.subTest(values=values):
                self.row.update(visa_number=None, force_rescrape=False, max_films=1)
                self.row.update(values)
                with self.assertRaises(ValueError):
                    self.dispatch()
        self.client.create_flow_run_from_deployment.assert_not_called()

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
    def test_target_pipeline_order_and_failure_short_circuit(self):
        for failure in (None, "airbyte", "scrape", "dbt"):
            calls = Mock()
            if failure:
                getattr(calls, failure).side_effect = RuntimeError(failure)
            with patch.object(flows.IngestionRequestSettings, "from_env", return_value="settings"), \
                    patch.object(flows, "_mark_request_processing", calls.processing), \
                    patch.object(flows, "_run_airbyte_sync_step", calls.airbyte), \
                    patch.object(flows, "_run_allocine_scraping_step", calls.scrape), \
                    patch.object(flows, "_run_dbt_phase_2_step", calls.dbt), \
                    patch.object(flows, "_mark_request_success", calls.success), \
                    patch.object(flows, "_mark_request_failed", calls.failed):
                kwargs = dict(request_id=str(uuid4()), visa_number="144246", force_rescrape=True,
                              airbyte_connection_names=["Sheets"])
                if failure:
                    with self.assertRaisesRegex(RuntimeError, failure):
                        flows.run_allocine_scraping.fn(**kwargs)
                else:
                    flows.run_allocine_scraping.fn(**kwargs)
            stages = ["processing", "airbyte", "scrape", "dbt", "success"]
            expected = stages if failure is None else stages[:stages.index(failure) + 1] + ["failed"]
            self.assertEqual([c[0] for c in calls.mock_calls], expected)
            calls.airbyte.assert_called_once_with(enabled=True, connection_names=["Sheets"])
            if failure != "airbyte":
                calls.scrape.assert_called_once_with(config_path=str(flows.ALLOCINE_CONFIG_PATH),
                                                    max_films=1, visa_number="144246", force_rescrape=True)

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

    def test_batch_airbyte_failure_stops_scraping_and_publication(self):
        with patch.object(flows, "_run_airbyte_sync_step", side_effect=RuntimeError("sync failed")) as airbyte, \
                patch.object(flows, "_run_allocine_scraping_step") as scrape, \
                patch.object(flows, "_run_dbt_phase_2_step") as dbt:
            with self.assertRaisesRegex(RuntimeError, "sync failed"):
                flows.run_allocine_scraping.fn(max_films=27, airbyte_connection_names=["Sheets"])
        airbyte.assert_called_once_with(enabled=True, connection_names=["Sheets"])
        scrape.assert_not_called()
        dbt.assert_not_called()

    def test_batch_syncs_before_scraping_without_automatic_dbt(self):
        calls = Mock()
        with patch.object(flows, "_run_airbyte_sync_step", calls.airbyte), \
                patch.object(flows, "_run_allocine_scraping_step", calls.scrape), \
                patch.object(flows, "_run_dbt_phase_2_step", calls.dbt):
            flows.run_allocine_scraping.fn(max_films=27, airbyte_connection_names=["Sheets"])
        self.assertEqual([c[0] for c in calls.mock_calls], ["airbyte", "scrape"])
        calls.airbyte.assert_called_once_with(enabled=True, connection_names=["Sheets"])
        calls.scrape.assert_called_once_with(config_path=str(flows.ALLOCINE_CONFIG_PATH), max_films=27)

    def test_success_and_failure_are_written_after_scraping(self):
        request_id = uuid4()
        for exception in (None, RuntimeError("browser unavailable")):
            calls = Mock()
            calls.scrape.side_effect = exception
            with patch.object(flows.IngestionRequestSettings, "from_env", return_value="settings"), \
                    patch.object(flows, "_mark_request_processing", calls.processing), \
                    patch.object(flows, "_run_airbyte_sync_step", calls.airbyte), \
                    patch.object(flows, "_run_allocine_scraping_step", calls.scrape), \
                    patch.object(flows, "_mark_request_success", calls.success), \
                    patch.object(flows, "_mark_request_failed", calls.failed):
                if exception:
                    with self.assertRaisesRegex(RuntimeError, "browser unavailable"):
                        flows.run_allocine_scraping.fn(max_films=27, request_id=str(request_id))
                else:
                    flows.run_allocine_scraping.fn(max_films=27, request_id=str(request_id))
            self.assertEqual([c[0] for c in calls.mock_calls],
                             ["processing", "airbyte", "scrape", "failed" if exception else "success"])
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

    def test_buttons_and_cards_reserve_existing_tutorial_and_introduction(self):
        dashboard = {"dashcards": [
            {"row": 0, "size_y": 2, "visualization_settings": {"text": "Guide métier : revue humaine Allociné"}},
            {"row": 2, "size_y": 9, "visualization_settings": {"text": "## Examiner le scraping Allociné"}},
            {"row": 50, "size_y": 5, "card_id": 83},
        ]}
        self.assertEqual(review.header_offset(dashboard), 11)
        self.assertEqual(review.header_offset({}), 0)

    def test_second_action_targets_one_visa_and_preserves_batch_button(self):
        body = review.action_body(3, 38, targeted=True)
        tags = body["dataset_query"]["native"]["template-tags"]
        self.assertEqual(set(tags), {"email", "reason", "visa_number", "force_rescrape"})
        self.assertEqual(tags["force_rescrape"]["default"], "Non")
        self.assertEqual(body["visualization_settings"]["fields"]["force_rescrape"]["valueOptions"], ["Non", "Oui"])
        self.assertIn("'metabase:allocine'", body["dataset_query"]["native"]["query"])
        batch = review.action_placement(2, 12)
        targeted = review.action_placement(3, 13, targeted=True)
        self.assertEqual((batch["col"], batch["size_x"], targeted["col"], targeted["size_x"]), (0, 12, 12, 12))
        self.assertEqual(targeted["parameter_mappings"], [])

    def test_action_requires_identity_reason_and_positive_integer_limit(self):
        body = review.action_body(3, 38)
        tags = body["dataset_query"]["native"]["template-tags"]
        self.assertEqual(set(tags), {"email", "reason", "max_films"})
        self.assertTrue(all(tag["required"] for tag in tags.values()))
        self.assertEqual(tags["max_films"]["default"], 10)
        self.assertEqual(review.action_placement(9, -10)["parameter_mappings"], [])


if __name__ == "__main__":
    unittest.main()
