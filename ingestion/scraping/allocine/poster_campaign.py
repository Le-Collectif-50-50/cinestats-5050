"""Backfill local par lots, avec export SQL atomique après chaque lot."""

import argparse
import asyncio
import json
import os
import signal
from pathlib import Path

from sqlalchemy import create_engine

from ingestion.scraping.allocine.connector import AllocineAirbyteSource, ConnectorConfig
from ingestion.scraping.allocine.main import DEFAULT_ENV_PATH, _load_dotenv, _load_json
from ingestion.scraping.allocine.poster_backfill import process_candidates, select_candidates
from ingestion.scraping.allocine.poster_export import export_posters


def run_campaign(raw_config, output_dir, batch_size=10):
    if batch_size < 1:
        raise ValueError("batch_size doit être positif")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Chaque campagne possède son dossier ; pas de double lancement ni d'écrasement.
    with (output_dir / "campaign.pid").open("x") as handle:
        handle.write(str(os.getpid()))
    stopped = False

    def request_stop(*_):
        nonlocal stopped
        stopped = True

    previous_handlers = {
        signum: signal.signal(signum, request_stop)
        for signum in (signal.SIGINT, signal.SIGTERM)
    }
    config = ConnectorConfig.from_dict(raw_config)
    engine = create_engine(config.database_url)
    state = {"processed": 0, "updated": 0, "missing": 0, "error": 0, "unchanged": 0}

    def checkpoint():
        temporary = output_dir / "posters.pending.sql"
        temporary.unlink(missing_ok=True)
        state["exported"] = export_posters(raw_config, temporary)
        temporary.replace(output_dir / "posters.sql")
        (output_dir / "progress.json").write_text(json.dumps(state, indent=2) + "\n")
        print(json.dumps(state), flush=True)

    try:
        with engine.connect() as connection:
            candidates = select_candidates(connection, config)
        state["selected"] = len(candidates)
        # Sélection figée : aucune boucle infinie sur les affiches absentes.
        (output_dir / "candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
        scraper, browser_factory = AllocineAirbyteSource()._load_scraping_dependencies()
        checkpoint()
        for start in range(0, len(candidates), batch_size):
            if stopped or (output_dir / "STOP").exists():
                state["status"] = "stopped"
                break
            results = asyncio.run(
                process_candidates(
                    engine,
                    config,
                    candidates[start : start + batch_size],
                    scraper,
                    browser_factory,
                )
            )
            for result in results:
                state["processed"] += 1
                state[result["status"]] += 1
            checkpoint()
            if results and all(result["status"] == "error" for result in results):
                state["status"] = "stopped_on_errors"
                break
        else:
            state["status"] = "complete"
        checkpoint()
        return state
    finally:
        engine.dispose()
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=10)
    args = parser.parse_args()
    _load_dotenv(DEFAULT_ENV_PATH)
    raw = _load_json(args.config)
    # Cette commande exécute toujours Chromium sur la machine locale.
    raw["playwright_ws_endpoint"] = None
    state = run_campaign(raw, args.output_dir, args.batch_size)
    return 1 if state["error"] or state["status"] != "complete" else 0


if __name__ == "__main__":
    raise SystemExit(main())
