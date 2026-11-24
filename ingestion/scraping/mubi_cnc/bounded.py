"""Lots séparés, bornés en durée et reprenables depuis les checkpoints PostgreSQL."""

import asyncio
import json
import time
from dataclasses import replace
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from .connector import (
    ConnectorConfig,
    MubiCncAirbyteSource,
    _ensure_schema,
    _ensure_film_awards_table,
    _ensure_festival_films_table,
    _fetch_pending_mubi_ids,
    _fetch_referenced_editions,
    _pending_edition_pages,
    _relation,
)


def pending_work(raw_config):
    config = ConnectorConfig.from_dict(raw_config)
    engine = create_engine(config.database_url)
    try:
        with engine.connect() as conn:
            ids = _fetch_pending_mubi_ids(conn, config)
            editions = _fetch_referenced_editions(conn, config)
            pages = _pending_edition_pages(conn, config, editions)
        return {"film_ids": ids, "festival_pages": len(pages)}
    finally:
        engine.dispose()


async def collect_phase(source, config, phase, page_limit, seconds):
    budget = asyncio.timeout(seconds)
    try:
        async with budget:
            if phase == "awards":
                await source._scrape_cnc_film_awards(config)
            else:
                engine = create_engine(config.database_url)
                try:
                    with engine.connect() as conn:
                        editions = _fetch_referenced_editions(conn, config)
                finally:
                    engine.dispose()
                await source._scrape_festival_editions(config, editions, page_limit=page_limit)
    except TimeoutError:
        if not budget.expired():
            raise
        # Les pages/films achevés sont déjà persistés. Le suivant reste éligible.
        return True
    return False


def run_phase(raw_config, *, phase, page_limit=25, job_timeout_seconds=900):
    if phase not in {"awards", "festivals"}:
        raise ValueError("Phase attendue : awards ou festivals")
    for name, value in (
        ("page_limit", page_limit),
        ("job_timeout_seconds", job_timeout_seconds),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} doit être un entier strictement positif")
    if job_timeout_seconds > 900:
        raise ValueError("Un lot ne peut dépasser 900 secondes de collecte")
    config = ConnectorConfig.from_dict(raw_config)
    if phase == "awards" and config.scrape_limit is None:
        config = replace(config, scrape_limit=10)
    url = make_url(config.database_url)
    if url.get_backend_name() == "postgresql":
        config = replace(
            config,
            database_url=url.update_query_dict(
                {
                    "connect_timeout": "15",
                    "options": "-c statement_timeout=30000 -c lock_timeout=10000",
                }
            ).render_as_string(hide_password=False),
        )
    source = MubiCncAirbyteSource()
    source.run_id = str(uuid4())
    engine = create_engine(config.database_url)
    started = time.monotonic()
    try:
        with engine.connect() as guard:
            locked = False
            if url.get_backend_name() == "postgresql":
                locked = guard.execute(
                    text("SELECT pg_try_advisory_lock(17891,5050)")
                ).scalar_one()
                guard.commit()
                if not locked:
                    raise RuntimeError("Un autre lot Mubi est déjà actif")
            try:
                _ensure_schema(guard, config.output_schema)
                _ensure_film_awards_table(guard, config)
                _ensure_festival_films_table(guard, config)
                guard.commit()
                exhausted = asyncio.run(
                    collect_phase(source, config, phase, page_limit, job_timeout_seconds)
                )
                table = (
                    config.film_awards_table
                    if phase == "awards"
                    else config.festival_films_table
                )
                statuses = dict(
                    guard.execute(
                        text(
                            f"SELECT scrape_status,count(*) FROM {_relation(config.output_schema, table)} "
                            "WHERE run_id=:run_id GROUP BY scrape_status"
                        ),
                        {"run_id": source.run_id},
                    ).all()
                )
                if statuses.get("error", 0) or statuses.get("blocked", 0):
                    raise RuntimeError(
                        f"Collecte Mubi incomplète : {statuses} ; checkpoints conservés"
                    )
            finally:
                if locked:
                    guard.rollback()
                    guard.execute(text("SELECT pg_advisory_unlock(17891,5050)"))
                    guard.commit()
        result = {
            "phase": phase,
            "run_id": source.run_id,
            "budget_exhausted": exhausted,
            "statuses": statuses,
            "seconds": round(time.monotonic() - started, 2),
        }
        print("Mubi bounded summary: " + json.dumps(result, ensure_ascii=False), flush=True)
        return result
    finally:
        engine.dispose()
