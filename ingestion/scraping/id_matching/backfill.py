"""Planifier un rattrapage fini, avec une liste explicite de visas par run Prefect."""

import argparse
import asyncio
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

from .__main__ import database_url, load_references, references
from .store import check_tables, exclude_processed

DEPLOYMENT = "Rechercher les identifiants MUBI et TMDB/rechercher-identifiants-manquants"


def plan_batches(pending, start, *, batch_size=10, interval_minutes=15, excluded=()):
    if start.tzinfo is None or batch_size < 1 or interval_minutes < 1:
        raise ValueError("Date avec fuseau, taille et intervalle positifs requis")
    remaining = [ref.visa for ref, _ in pending if ref.visa not in set(excluded)]
    return [
        (
            start + timedelta(minutes=interval_minutes * i),
            remaining[offset : offset + batch_size],
        )
        for i, offset in enumerate(range(0, len(remaining), batch_size))
    ]


async def schedule(
    pending,
    *,
    campaign,
    start,
    batch_size=10,
    interval_minutes=15,
    apply=False,
    wait_for_flow_run_id=None,
):
    from prefect.client.orchestration import get_client
    from prefect.client.schemas.filters import FlowRunFilter, FlowRunFilterTags
    from prefect.states import Scheduled

    if not campaign or start.tzinfo is None:
        raise ValueError("Campagne et date avec fuseau requises")
    async with get_client() as client:
        deployment = await client.read_deployment_by_name(DEPLOYMENT)
        concurrency = deployment.global_concurrency_limit
        if concurrency is None or concurrency.limit != 1 or not concurrency.active:
            raise ValueError("Le déploiement doit avoir une concurrence active limitée à 1")
        # Pagination : une campagne peut contenir plus de 200 runs.
        existing = []
        offset = 0
        while True:
            page = await client.read_flow_runs(
                flow_run_filter=FlowRunFilter(tags=FlowRunFilterTags(all_=[campaign])),
                limit=200,
                offset=offset,
            )
            existing.extend(page)
            if len(page) < 200:
                break
            offset += 200
        excluded = {visa for run in existing for visa in run.parameters.get("visa_numbers", [])}
        latest = max(
            (r.expected_start_time for r in existing if r.expected_start_time), default=None
        )
        if latest:
            start = max(start, latest + timedelta(minutes=interval_minutes))
        plan = plan_batches(
            pending,
            start,
            batch_size=batch_size,
            interval_minutes=interval_minutes,
            excluded=excluded,
        )
        report = {
            "campaign": campaign,
            "existing_runs": len(existing),
            "new_runs": len(plan),
            "visas": sum(len(visas) for _, visas in plan),
            "first_start": plan[0][0].isoformat() if plan else None,
            "last_start": plan[-1][0].isoformat() if plan else None,
            "applied": apply,
        }
        searches_by_visa = {reference.visa: len(providers) for reference, providers in pending}
        report["provider_searches"] = sum(
            searches_by_visa[v] for _, visas in plan for v in visas
        )
        report["pilot_extrapolation_hours"] = round(report["provider_searches"] * 24 / 3600, 1)
        if apply:
            if start <= datetime.now(timezone.utc):
                raise ValueError("La première exécution doit être planifiée dans le futur")
            for i, (when, visas) in enumerate(plan, len(existing) + 1):
                fingerprint = hashlib.sha256("|".join(visas).encode()).hexdigest()
                searches = sum(searches_by_visa[v] for v in visas)
                minutes = math.ceil(searches * 24 / 60)
                await client.create_flow_run_from_deployment(
                    deployment.id,
                    parameters={
                        "provider": "all",
                        "max_films": batch_size,
                        "visa_numbers": visas,
                        "skip_processed": True,
                        "max_candidates": 10,
                        "dry_run": False,
                        "wait_for_flow_run_id": wait_for_flow_run_id,
                    },
                    state=Scheduled(scheduled_time=when),
                    name=f"{campaign}-lot-{i:03d}-env-{minutes}min",
                    context={
                        "matching_estimate": {
                            "provider_searches": searches,
                            "estimated_minutes": minutes,
                            "seconds_per_search": 24,
                        }
                    },
                    tags=[campaign, "id-matching-backfill"],
                    idempotency_key=f"{campaign}:{fingerprint}",
                )
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--start", required=True, type=datetime.fromisoformat)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--interval-minutes", type=int, default=15)
    parser.add_argument(
        "--wait-for-flow-run-id", help="Attendre ce run avant d'ouvrir un navigateur"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Créer les runs ; sinon afficher le plan"
    )
    args = parser.parse_args()
    if args.batch_size < 1 or args.interval_minutes < 1 or args.start.tzinfo is None:
        parser.error("Taille, intervalle positifs et date avec fuseau requis")
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    engine = create_engine(database_url())
    try:
        check_tables(engine)
        rows, films = load_references(engine)
        pending = exclude_processed(engine, list(references(rows, films, ("mubi", "tmdb"))))
    finally:
        engine.dispose()
    report = asyncio.run(
        schedule(
            pending,
            campaign=args.campaign,
            start=args.start,
            batch_size=args.batch_size,
            interval_minutes=args.interval_minutes,
            apply=args.apply,
            wait_for_flow_run_id=args.wait_for_flow_run_id,
        )
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
