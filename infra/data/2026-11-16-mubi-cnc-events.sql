-- Reprise durable de la phase éditions Mubi, sans changement des lignes historiques.
-- Exécuter sur la base courante avec le propriétaire de raw.mubi_film_awards.
BEGIN;
ALTER TABLE raw.mubi_film_awards
  ADD COLUMN IF NOT EXISTS event_slug text,
  ADD COLUMN IF NOT EXISTS event_type text;
COMMIT;
