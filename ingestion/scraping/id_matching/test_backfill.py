"""Reprise et campagne finie, sans base ni serveur Prefect."""

import asyncio
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from ingestion.scraping.id_matching.backfill import plan_batches, schedule
from ingestion.scraping.id_matching.identity import Film
from ingestion.scraping.id_matching.store import exclude_processed


def pending(count):
    return [
        (Film("cnc", str(i), f"Film {i}", ["Nom Prénom"], visa=str(i)), ["mubi", "tmdb"])
        for i in range(1, count + 1)
    ]


def test_plan_covers_each_visa_once_and_has_finite_end():
    start = datetime(2026, 11, 16, 4, tzinfo=timezone.utc)
    batches = plan_batches(
        pending(23), start, batch_size=10, interval_minutes=15, excluded={"1"}
    )
    assert [len(visas) for _, visas in batches] == [10, 10, 2]
    flattened = [visa for _, visas in batches for visa in visas]
    assert len(flattened) == len(set(flattened)) == 22
    assert "1" not in flattened
    assert batches[-1][0] == start + timedelta(minutes=30)


def test_resume_is_per_provider_and_reference():
    entries = pending(2)
    reference = entries[0][0]

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, query):
            assert "WHERE status IN ('a_revoir', 'ambigu', 'non_trouve')" in str(query)
            return [
                ("1", "mubi", asdict(reference)),
                ("2", "tmdb", asdict(replace(entries[1][0], title="Ancien titre"))),
            ]

    result = exclude_processed(SimpleNamespace(connect=Connection), entries)
    assert result[0][1] == ["tmdb"]
    assert result[1][1] == ["mubi", "tmdb"]


@pytest.fixture
def client(monkeypatch):
    client = SimpleNamespace(
        read_deployment_by_name=AsyncMock(
            return_value=SimpleNamespace(
                id=uuid4(), global_concurrency_limit=SimpleNamespace(limit=1, active=True)
            )
        ),
        read_flow_runs=AsyncMock(return_value=[]),
        create_flow_run_from_deployment=AsyncMock(),
    )
    context = AsyncMock()
    context.__aenter__.return_value = client
    monkeypatch.setattr("prefect.client.orchestration.get_client", lambda: context)
    return client


def test_schedule_dry_run_does_not_create_runs(client):
    report = asyncio.run(
        schedule(
            pending(3),
            campaign="test-campaign",
            start=datetime.now(timezone.utc) + timedelta(hours=1),
            batch_size=2,
        )
    )
    assert report["new_runs"] == 2 and report["visas"] == 3
    client.create_flow_run_from_deployment.assert_not_awaited()


def test_schedule_preserves_existing_targets_and_uses_explicit_visas(client):
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    client.read_flow_runs.return_value = [
        SimpleNamespace(parameters={"visa_numbers": ["1"]}, expected_start_time=start)
    ]
    report = asyncio.run(
        schedule(pending(3), campaign="test-campaign", start=start, batch_size=2, apply=True)
    )
    assert report["existing_runs"] == 1 and report["new_runs"] == 1
    call = client.create_flow_run_from_deployment.call_args.kwargs
    assert call["parameters"]["visa_numbers"] == ["2", "3"]
    assert call["parameters"]["skip_processed"] is True
    assert call["parameters"]["dry_run"] is False
    assert call["state"].state_details.scheduled_time == start + timedelta(minutes=15)
    assert "test-campaign" in call["tags"]
    assert call["idempotency_key"].startswith("test-campaign:")


def test_schedule_rejects_concurrency_above_one(client):
    client.read_deployment_by_name.return_value.global_concurrency_limit.limit = 2
    with pytest.raises(ValueError):
        asyncio.run(
            schedule(pending(3), campaign="test", start=datetime.now(timezone.utc), apply=True)
        )
    client.create_flow_run_from_deployment.assert_not_awaited()
