"""Export SQL ciblé des affiches récupérées, import atomique et rejouable."""

import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy import create_engine, text

from ingestion.scraping.allocine.connector import ConnectorConfig, _relation
from ingestion.scraping.allocine.main import DEFAULT_ENV_PATH, _load_dotenv, _load_json


def render_import(rows):
    """Données encodées en JSON dans une chaîne dollar-quoted sans interpolation SQL."""
    payload = json.dumps(rows, ensure_ascii=False, default=str)
    delimiter = "$poster_" + uuid.uuid4().hex + "$"
    while delimiter in payload:
        delimiter = "$poster_" + uuid.uuid4().hex + "$"
    return f"""-- Affiches Allociné uniquement. Appliquer la migration poster_url au préalable.
-- Exécuter avec psql -X -v ON_ERROR_STOP=1 -f ce_fichier.sql
BEGIN;
SET LOCAL lock_timeout = '10s';
CREATE TEMP TABLE allocine_poster_import ON COMMIT DROP AS
SELECT * FROM jsonb_to_recordset({delimiter}{payload}{delimiter}::jsonb) AS p(
    source_record_id text, allocine_id integer, poster_url text,
    run_id text, attempted_at timestamptz, source_url text
);
CREATE UNIQUE INDEX ON allocine_poster_import (source_record_id, allocine_id);
WITH updated AS (
    UPDATE raw.allocine_data AS d SET poster_url = p.poster_url
    FROM allocine_poster_import p
    WHERE d.source_record_id = p.source_record_id AND d.allocine_id = p.allocine_id
      AND d.scrape_status = 'success' AND d.poster_url IS NULL
      AND NULLIF(p.poster_url, '') IS NOT NULL
    RETURNING d.source_record_id, d.allocine_id
), counts AS (
    SELECT source_record_id, allocine_id, count(*)::integer AS updated_rows
    FROM updated GROUP BY source_record_id, allocine_id
)
INSERT INTO raw.allocine_data_poster_backfill
    (run_id, attempted_at, source_record_id, allocine_id, source_url,
     poster_url, status, error_message, updated_rows)
SELECT p.run_id, p.attempted_at, p.source_record_id, p.allocine_id, p.source_url,
       p.poster_url, 'updated', NULL, c.updated_rows
FROM allocine_poster_import p JOIN counts c USING (source_record_id, allocine_id);
COMMIT;
"""


def export_posters(raw_config, output, run_id=None):
    config = ConnectorConfig.from_dict(raw_config)
    table = _relation(config.output_schema, config.output_table)
    audit = _relation(config.output_schema, config.output_table + "_poster_backfill")
    engine = create_engine(config.database_url)
    try:
        with engine.connect() as connection:
            rows = [
                dict(row)
                for row in connection.execute(
                    text(
                        f"""
                SELECT DISTINCT ON (a.source_record_id, a.allocine_id)
                    a.source_record_id, a.allocine_id, a.poster_url,
                    a.run_id, a.attempted_at, a.source_url
                FROM {audit} a
                WHERE a.status = 'updated' AND NULLIF(a.poster_url, '') IS NOT NULL
                  AND (CAST(:run_id AS text) IS NULL OR a.run_id = :run_id)
                  AND EXISTS (
                    SELECT 1 FROM {table} d
                    WHERE d.source_record_id = a.source_record_id
                      AND d.allocine_id = a.allocine_id
                      AND d.scrape_status = 'success' AND d.poster_url = a.poster_url
                  )
                ORDER BY a.source_record_id, a.allocine_id,
                         a.attempted_at DESC, a.attempt_id DESC
            """
                    ),
                    {"run_id": run_id},
                ).mappings()
            ]
        # Refuser d'écraser un export précédent.
        with Path(output).open("x", encoding="utf-8") as handle:
            handle.write(render_import(rows))
        return len(rows)
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    _load_dotenv(DEFAULT_ENV_PATH)
    count = export_posters(_load_json(args.config), args.output, args.run_id)
    print(f"{count} affiches exportées vers {args.output}")


if __name__ == "__main__":
    main()
