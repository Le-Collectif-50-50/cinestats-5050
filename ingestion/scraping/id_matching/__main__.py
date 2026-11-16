"""Lit raw.id_matching et journalise les propositions MUBI/TMDB dans ops."""

import argparse
import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

from .identity import Film, norm, number


def missing(value):
    # Une valeur présente mais invalide n'est jamais remplacée implicitement.
    return value is None or not str(value).strip()


def references(rows, films, providers, visa=None, visas=None):
    allowed = set(visas) if visas is not None else ({visa} if visa is not None else None)
    grouped = defaultdict(list)
    for row in rows:
        key = number(row.get("VISA"))
        if key and (allowed is None or key in allowed):
            grouped[key].append(row)
    directors = defaultdict(set)
    for row in films:
        key = number(row.get("VISA"))
        value = str(row.get("REALISATEUR") or "").strip()
        directors[key].add(value)
    for key, entries in sorted(grouped.items(), key=lambda pair: int(pair[0])):
        titles = {str(row.get("TITRE") or "").strip() for row in entries}
        names = directors.get(key, set())
        # Références contradictoires, y compris une référence vide : revue obligatoire.
        name = next(iter(names)) if len(names) == 1 else ""
        people = [
            p.strip() for p in re.split(r"\s*(?:;|,|\n|\s+et\s+|\s+&\s+)\s*", name) if norm(p)
        ]
        title = next(iter(titles)) if len(titles) == 1 else ""
        pending = [
            p for p in providers if all(missing(row.get("ID_" + p.upper())) for row in entries)
        ]
        if pending:
            yield Film("cnc", key, title, people, visa=key), pending


def database_url():
    if os.getenv("ID_MATCHING_DATABASE_URL"):
        return os.environ["ID_MATCHING_DATABASE_URL"]
    required = (
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "SCRAPER_POSTGRES_USER",
        "SCRAPER_POSTGRES_PASSWORD",
    )
    if any(not os.getenv(key) for key in required):
        raise ValueError(
            "Configurer ID_MATCHING_DATABASE_URL ou les variables POSTGRES/SCRAPER."
        )
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["SCRAPER_POSTGRES_USER"],
        password=os.environ["SCRAPER_POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
        query={"sslmode": os.getenv("POSTGRES_SSLMODE", "require")},
    )


def load_references(engine):
    # Pas de DDL, aucune écriture ; PostgreSQL impose le mode lecture seule.
    with engine.connect() as connection, connection.begin():
        connection.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        rows = [
            row[0]
            for row in connection.execute(text("SELECT to_jsonb(i) FROM raw.id_matching i"))
        ]
        films = [
            row[0] for row in connection.execute(text("SELECT to_jsonb(f) FROM raw.films f"))
        ]
    return rows, films


async def run(args, pending, engine):
    from .matching import match
    from .navigation import Browser
    from .store import save_result

    failed = False
    run_id = uuid4()
    print(f"run_id={run_id}", file=sys.stderr)
    async with Browser(
        ws_endpoint=os.getenv("PLAYWRIGHT_WS_ENDPOINT") or None,
        headless=not args.headed,
        lightweight=True,
    ) as browser:
        for reference, providers in pending:
            for provider in providers:
                result = await match(
                    browser, reference, provider, max_candidates=args.max_candidates
                )
                if not args.dry_run:
                    save_result(engine, run_id, result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                failed |= result["status"] in {"erreur", "bloque"}
    return int(failed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("mubi", "tmdb", "all"), default="all")
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument("--visa", type=number)
    targets.add_argument("--visas", nargs="+", type=number)
    parser.add_argument(
        "--skip-processed",
        action="store_true",
        help="Ignorer les conclusions déjà enregistrées pour la même référence",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Nombre maximal de visas (défaut 10)"
    )
    parser.add_argument("--max-candidates", type=int, default=10)
    parser.add_argument(
        "--inspect", action="store_true", help="Compter sans ouvrir de navigateur"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Recherche avec résultats stdout, sans écriture ops",
    )
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args(argv)
    if (
        args.limit < 1
        or args.max_candidates < 1
        or args.visa == ""
        or (args.visas is not None and "" in args.visas)
    ):
        parser.error("Visa, limite et nombre de candidats doivent être strictement positifs.")
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    engine = create_engine(database_url())
    try:
        rows, films = load_references(engine)
        providers = ("mubi", "tmdb") if args.provider == "all" else (args.provider,)
        pending = list(references(rows, films, providers, args.visa, args.visas))
        if args.skip_processed:
            from .store import exclude_processed

            pending = exclude_processed(engine, pending)
        print(
            json.dumps(
                {
                    "eligible_visas": len(pending),
                    "selected_visas": min(len(pending), args.limit),
                    "missing_ids": {p: sum(p in ps for _, ps in pending) for p in providers},
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        if args.inspect or not pending:
            return 0
        if not args.dry_run:
            from .store import check_tables

            check_tables(engine)
        return asyncio.run(run(args, pending[: args.limit], engine))
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Les exceptions SQLAlchemy peuvent contenir identifiants et paramètres.
        print(
            f"Échec ({type(exc).__name__}) : vérifier configuration, accès et dépendances.",
            file=sys.stderr,
        )
        sys.exit(1)
