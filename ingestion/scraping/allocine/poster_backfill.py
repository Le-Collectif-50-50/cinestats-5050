"""Complément explicite des affiches, sans modifier les collectes initiales."""

import asyncio
import random
import uuid

from sqlalchemy import bindparam, create_engine, text

from ingestion.scraping.allocine.connector import (
    AllocineAirbyteSource,
    ConnectorConfig,
    _relation,
)


def select_candidates(connection, config, source_ids=None, limit=None):
    """Une requête par couple source/Allociné ; anciennes tentatives en dernier."""
    if limit is not None and limit < 1:
        raise ValueError("limit doit être positif")
    table = _relation(config.output_schema, config.output_table)
    audit = _relation(config.output_schema, config.output_table + "_poster_backfill")
    filters = "AND d.source_record_id IN :source_ids" if source_ids else ""
    query = text(
        f"""
        SELECT d.source_record_id, d.allocine_id
        FROM {table} d
        LEFT JOIN {audit} a ON a.source_record_id = d.source_record_id
                           AND a.allocine_id = d.allocine_id
        WHERE d.scrape_status = 'success' AND d.poster_url IS NULL
          AND d.source_record_id IS NOT NULL AND d.allocine_id > 0
          {filters}
        GROUP BY d.source_record_id, d.allocine_id
        ORDER BY max(a.attempted_at) NULLS FIRST, d.source_record_id, d.allocine_id
        LIMIT :limit
    """
    )
    if source_ids:
        query = query.bindparams(bindparam("source_ids", expanding=True))
    return [
        dict(row._mapping)
        for row in connection.execute(query, {"source_ids": source_ids, "limit": limit})
    ]


def save_attempt(connection, config, attempt):
    """Mise à jour conditionnelle et audit dans la même transaction par film."""
    table = _relation(config.output_schema, config.output_table)
    audit = _relation(config.output_schema, config.output_table + "_poster_backfill")
    attempt = dict(attempt)
    attempt["updated_rows"] = 0
    if attempt["poster_url"]:
        result = connection.execute(
            text(
                f"""
            UPDATE {table} SET poster_url = :poster_url
            WHERE source_record_id = :source_record_id AND allocine_id = :allocine_id
              AND scrape_status = 'success' AND poster_url IS NULL
        """
            ),
            attempt,
        )
        attempt["updated_rows"] = result.rowcount
        attempt["status"] = "updated" if result.rowcount else "unchanged"
    connection.execute(
        text(
            f"""
        INSERT INTO {audit}
          (run_id, source_record_id, allocine_id, source_url, poster_url,
           status, error_message, updated_rows)
        VALUES (:run_id, :source_record_id, :allocine_id, :source_url, :poster_url,
                :status, :error_message, :updated_rows)
    """
        ),
        attempt,
    )
    return attempt


async def process_candidates(engine, config, candidates, scraper, browser_factory):
    run_id = str(uuid.uuid4())
    results = []
    for index, candidate in enumerate(candidates):
        attempt = dict(
            candidate,
            run_id=run_id,
            poster_url=None,
            status="missing",
            error_message=None,
            source_url=scraper.FILM_URL.format(allocine_film_id=candidate["allocine_id"]),
        )

        async def fetch_poster(source_url=attempt["source_url"]):
            # Session indépendante : une panne navigateur ne contamine pas le film suivant.
            async with browser_factory(
                ws_endpoint=config.playwright_ws_endpoint,
                headless=config.headless,
                debug_pause_between_actions=config.debug_pause_between_actions,
                verbose=config.verbose,
            ) as session:
                html = await session.fetch_html(source_url)
                return scraper.extract_film_details(html).get("poster_url") or None

        try:
            attempt["poster_url"] = await asyncio.wait_for(
                fetch_poster(), timeout=config.record_timeout_seconds or None
            )
        except Exception as exc:
            attempt["status"] = "error"
            attempt["error_message"] = f"{type(exc).__name__}: {exc}"

        try:
            with engine.begin() as connection:
                attempt = save_attempt(connection, config, attempt)
        except Exception as exc:
            # SQLAlchemy peut inclure des paramètres : ne pas imprimer l'exception.
            attempt["status"] = "error"
            attempt["error_message"] = f"Écriture SQL annulée ({type(exc).__name__})"
            attempt["updated_rows"] = 0
        print(
            f"poster_backfill run={run_id} source={candidate['source_record_id']} "
            f"allocine={candidate['allocine_id']} status={attempt['status']} "
            f"updated_rows={attempt.get('updated_rows', 0)}",
            flush=True,
        )
        results.append(attempt)
        if index + 1 < len(candidates):
            await asyncio.sleep(
                random.uniform(
                    config.inter_film_delay_min_seconds, config.inter_film_delay_max_seconds
                )
            )
    return results


def backfill_posters(raw_config, *, dry_run=False, limit=None, source_ids=None):
    config = ConnectorConfig.from_dict(raw_config)
    engine = create_engine(config.database_url)
    try:
        with engine.connect() as connection:
            candidates = select_candidates(connection, config, source_ids, limit)
        if dry_run:
            # Aucune initialisation de table, aucun navigateur, aucune écriture.
            return candidates
        if not candidates:
            return []
        scraper, browser_factory = AllocineAirbyteSource()._load_scraping_dependencies()
        return asyncio.run(
            process_candidates(engine, config, candidates, scraper, browser_factory)
        )
    finally:
        engine.dispose()
