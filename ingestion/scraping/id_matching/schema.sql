-- Exécuter sur la base ingestion avec un rôle administrateur.
-- Les tables raw et le Google Sheet restent les sources canoniques.
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.id_matching_confirmed (
    run_id uuid NOT NULL,
    visa text NOT NULL,
    provider text NOT NULL CHECK (provider IN ('mubi', 'tmdb')),
    status text NOT NULL CHECK (status = 'trouve'),
    proposed_id text NOT NULL CHECK (proposed_id ~ '^[1-9][0-9]*$'),
    source_title text NOT NULL,
    reason text NOT NULL,
    checked_at timestamptz NOT NULL,
    evidence jsonb NOT NULL,
    PRIMARY KEY (run_id, visa, provider)
);

CREATE TABLE IF NOT EXISTS ops.id_matching_review (
    run_id uuid NOT NULL,
    visa text NOT NULL,
    provider text NOT NULL CHECK (provider IN ('mubi', 'tmdb')),
    status text NOT NULL CHECK (status IN ('a_revoir', 'ambigu', 'non_trouve', 'bloque', 'erreur')),
    proposed_id text CHECK (proposed_id IS NULL),
    source_title text NOT NULL,
    reason text NOT NULL,
    checked_at timestamptz NOT NULL,
    evidence jsonb NOT NULL,
    PRIMARY KEY (run_id, visa, provider)
);

CREATE INDEX IF NOT EXISTS id_matching_confirmed_latest
    ON ops.id_matching_confirmed (visa, provider, checked_at DESC);
CREATE INDEX IF NOT EXISTS id_matching_review_latest
    ON ops.id_matching_review (visa, provider, checked_at DESC);

-- Adapter le rôle si le script utilise un compte différent.
GRANT USAGE ON SCHEMA ops TO scraper_user;
GRANT SELECT, INSERT ON ops.id_matching_confirmed, ops.id_matching_review TO scraper_user;
GRANT USAGE ON SCHEMA ops TO metabase_ops_user;
GRANT SELECT ON ops.id_matching_confirmed, ops.id_matching_review TO metabase_ops_user;
