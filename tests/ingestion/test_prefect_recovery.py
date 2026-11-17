"""Reprise du worker sans serveur Prefect ni attente réelle."""

import contextlib
import io
import os
from pathlib import Path
import unittest
import urllib.error
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (ROOT / "ingestion/prefect/start_worker.sh").read_text()
PROBE = SCRIPT.split("python - <<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


class PrefectRecoveryTests(unittest.TestCase):
    def check_probe(self, responses, *, attempts, pauses, failure=False):
        with (
            patch.dict(os.environ, {"PREFECT_API_URL": "http://prefect-server:4200/api/"}),
            patch("urllib.request.urlopen", side_effect=responses) as request,
            patch("time.sleep") as sleep,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            if failure:
                with self.assertRaisesRegex(SystemExit, "60 tentatives"):
                    exec(compile(PROBE, "<api-readiness>", "exec"), {})
            else:
                exec(compile(PROBE, "<api-readiness>", "exec"), {})
            self.assertEqual(request.call_count, attempts)
            self.assertEqual(sleep.call_count, pauses)
            request.assert_called_with("http://prefect-server:4200/api/health", timeout=5)
            for call in sleep.call_args_list:
                self.assertEqual(call.args, (5,))

    def test_ready_api_does_not_delay_startup(self):
        self.check_probe([MagicMock()], attempts=1, pauses=0)

    def test_startup_recovers_from_connection_http_and_timeout_errors(self):
        for error in (
            urllib.error.URLError("DNS or connection unavailable"),
            urllib.error.HTTPError("http://unused", 503, "Unavailable", None, None),
            TimeoutError(),
            ConnectionResetError(),
        ):
            with self.subTest(error=type(error).__name__):
                self.check_probe([error, MagicMock()], attempts=2, pauses=1)

    def test_persistent_outage_exits_for_docker_to_retry(self):
        self.check_probe(
            [urllib.error.URLError("unavailable")] * 60,
            attempts=60,
            pauses=59,
            failure=True,
        )


if __name__ == "__main__":
    unittest.main()
