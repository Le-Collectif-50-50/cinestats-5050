# Setup infra reproductible - Airbyte OSS + dbt Core + Prefect avec Postgres distant

## Metadata du document

**Owner:** Joel Teixeira

**Last reviewed:** 2026-10-09

**Status:** active

## Historique du document

| #   | Date       | Author         | Observations                                            |
| --- | ---------- | -------------- | ------------------------------------------------------- |
| 1   | 2026-05-07 | Joel Teixeira  | Initial implementation                                  |
| 2   | 2026-05-22 | Joel Teixeira | Ajout du pinning de version Prefect et du troubleshooting de revision Alembic inconnue |
| 3   | 2026-05-26 | Joel Teixeira | Alignement avec les deployments Prefect actuels, le poller `ops.ingestion_run_requests` et les grants `ops` |
| 4   | 2026-10-06 | Joel Teixeira | Borne SQLAlchemy sous 2.1 pour corriger les erreurs du scheduler Prefect et procédure de reconstruction de l'image partagée. Ajout du compte Postgres dédié aux scrapers et de ses privilèges limités à `raw` |
| 5 | 2026-10-09 | Joel Teixeira | Formulaire Metabase natif avec identité déclarative et motif obligatoire, conservé dans la file d’ingestion. |

## 1. Objectif

Ce runbook décrit un parcours simple pour installer et exécuter la pipeline d'ingestion locale avec:

1. Airbyte OSS (`abctl`)
2. dbt Core (dans `prefect-worker`)
3. Prefect (UI + orchestration)
4. PostgreSQL distant (app + DB Prefect dédiée)

Objectif: avoir un setup reproductible, rapide à démarrer et facile à vérifier.

## 2. Topologie standard

Topologie cible en local:

1. Airbyte tourne localement via `abctl`.
2. `ingestion/docker-compose.yml` démarre:
   - `prefect-server`
   - `prefect-worker`
   - `browserless`
3. `prefect-worker` exécute:
   - `dbt` (phase 1, puis phase 2 optionnelle)
   - scraping Allociné via `ingestion/scraping/allocine/main.py`
   - le poller Prefect des demandes Metabase via `ops.ingestion_run_requests`
4. PostgreSQL distant héberge:
   - la base applicative (`raw`, `staging`, `intermediate`, `fnl`, `ops`)
   - la base dédiée `prefect`

Conventions utilisateurs:

1. `airbyte_user` pour la zone `raw`
2. `dbt_user` pour le runtime dbt
3. `prefect_user` pour la base `prefect` et les updates de lifecycle dans `ops.ingestion_run_requests`
4. `scraper_user` pour les scrapers standalone, limité aux tables nécessaires dans `raw`

## 3. Répertoire de travail

Depuis la racine du repo:

```bash
cd ingestion
```

Sauf mention contraire, toutes les commandes de ce runbook sont lancées depuis `ingestion/`.

## 4. Installation

### 4.1 Prérequis et vérification

Prérequis minimaux:

1. Docker + Docker Compose plugin
2. `curl`
3. `python3`
4. accès au serveur Postgres cible

Check rapide:

```bash
docker compose version
```

### 4.2 Contrat de variables d'environnement

Créer le fichier local:

```bash
cp .env.example .env
```

Variables indispensables à renseigner:

1. `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_SSLMODE`
2. `DBT_USER_POSTGRES_PASSWORD`, `SCRAPER_POSTGRES_USER` et `SCRAPER_POSTGRES_PASSWORD`
3. `PREFECT_VERSION`
4. `PREFECT_API_DATABASE_CONNECTION_URL`
5. `AIRBYTE_HOST`, `AIRBYTE_PORT`, `AIRBYTE_CLIENT_ID`, `AIRBYTE_CLIENT_SECRET`
6. `AIRBYTE_DESTINATION_POSTGRES_PASSWORD`
7. `PREFECT_AUTH_STRING`
8. `INGESTION_REQUEST_POSTGRES_PASSWORD`
9. `PREFECT_PORT` et `BROWSERLESS_PORT` si vous voulez des ports hôtes non défaut

Charger les variables dans le shell (optionnel):

```bash
set -a
source .env
set +a
```

### 4.3 Préparation utilisateurs et privilèges Postgres

À exécuter une fois par environnement (compte DBA):

```sql
CREATE USER airbyte_user WITH PASSWORD '<replace>';
CREATE USER dbt_user WITH PASSWORD '<replace>';
CREATE USER scraper_user WITH PASSWORD '<replace>';

GRANT CONNECT ON DATABASE reveler_inegalites_cinema TO airbyte_user;
GRANT CREATE, TEMPORARY ON DATABASE reveler_inegalites_cinema TO airbyte_user;
GRANT CONNECT ON DATABASE reveler_inegalites_cinema TO dbt_user;
GRANT CONNECT ON DATABASE reveler_inegalites_cinema TO scraper_user;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS fnl;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER SCHEMA raw OWNER TO airbyte_user;
ALTER SCHEMA staging OWNER TO dbt_user;
ALTER SCHEMA intermediate OWNER TO dbt_user;
ALTER SCHEMA fnl OWNER TO dbt_user;

GRANT USAGE, CREATE ON SCHEMA raw TO airbyte_user;
GRANT USAGE, CREATE ON SCHEMA raw TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA staging TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA intermediate TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA fnl TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA ops TO dbt_user;

-- Compte dédié aux scrapers : lecture source et écriture des seules sorties.
GRANT USAGE, CREATE ON SCHEMA raw TO scraper_user;
GRANT SELECT ON TABLE raw.id_matching TO scraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE raw.allocine_data TO scraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE raw.mubi_festival_films TO scraper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE raw.mubi_film_awards TO scraper_user;
```

Les trois derniers `GRANT` sont requis seulement si ces tables de sortie existent déjà et appartiennent à un autre rôle. Les tables créées par `scraper_user` lui appartiennent.

Base Prefect dédiée:

```sql
CREATE USER prefect_user WITH PASSWORD '<replace>';
CREATE DATABASE prefect OWNER prefect_user;
GRANT CONNECT ON DATABASE prefect TO prefect_user;
```

Table de demandes ingestion côté base projet:

```sql
CREATE TABLE IF NOT EXISTS ops.ingestion_run_requests (
  request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requested_at TIMESTAMP NOT NULL DEFAULT now(),
  requested_by_metabase_user TEXT NOT NULL,
  requested_by_metabase_group TEXT,
  request_reason TEXT,
  request_source TEXT NOT NULL DEFAULT 'metabase',
  request_status TEXT NOT NULL DEFAULT 'pending',
  claimed_at TIMESTAMP,
  claimed_by TEXT,
  processed_at TIMESTAMP,
  triggered_flow_run_id TEXT,
  trigger_error TEXT,
  dedupe_key TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ingestion_run_requests_status_requested_at
  ON ops.ingestion_run_requests (request_status, requested_at ASC);

DROP INDEX IF EXISTS ops.idx_ingestion_run_requests_dedupe_key_active;

CREATE UNIQUE INDEX idx_ingestion_run_requests_dedupe_key_active
  ON ops.ingestion_run_requests (dedupe_key)
  WHERE request_status IN ('pending', 'processing');

GRANT USAGE ON SCHEMA ops TO prefect_user;
GRANT SELECT, UPDATE ON ops.ingestion_run_requests TO prefect_user;
```

Exemple `.env`:

```bash
PREFECT_VERSION=3.8.7
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect_user:<replace>@<db-host>:<db-port>/prefect
PREFECT_AUTH_STRING=<user>:<password>
INGESTION_REQUEST_POSTGRES_USER=prefect_user
INGESTION_REQUEST_POSTGRES_PASSWORD=<replace>
SCRAPER_POSTGRES_USER=scraper_user
SCRAPER_POSTGRES_PASSWORD=<replace>
```

### Formulaire de déclenchement Metabase

Le bouton du dashboard `Pipeline Overview` ouvre l’action `Demander une ingestion` sur la connexion `cinestats-ops-db` (rôle `metabase_ops_user`). Le formulaire demande deux champs obligatoires :

- **Votre nom ou adresse e-mail** : variable texte `email`, enregistrée dans `requested_by_metabase_user`. Cette identité est déclarative ; elle n’est pas déduite de la session Metabase.
- **Motif de la demande** : variable texte `reason`, présentée comme **Texte long**, enregistrée dans `request_reason`.

Le SQL de l’action est versionné dans `infra/data/metabase-trigger-ingestion.sql`. Le libellé d’envoi est **Enregistrer la demande**. Une demande active pour la même journée empêche une nouvelle insertion, comme pour l’ancien bouton. Le poller et ses paramètres restent inchangés.

Sur une base existante, appliquer en propriétaire de la table ou administrateur :

```sql
ALTER TABLE ops.ingestion_run_requests
  ADD COLUMN IF NOT EXISTS request_reason TEXT;
```

La colonne reste nullable pour conserver les demandes historiques. Les scripts `infra/data/ops-ingestion-table.sql` et l’initialisation optionnelle du poller comprennent cette migration additive. Aucun droit supplémentaire n’est requis pour `metabase_ops_user`.

Après migration, synchroniser le schéma de `cinestats-ops-db` dans Metabase et afficher `request_reason` dans la question `Trigger / Ingestion Run Requests`. Les tests de configuration ne doivent pas soumettre de demande réelle : chaque ligne `pending` peut être prise en charge par Prefect.

### 4.4 Setup, configuration et bootstrap Airbyte

Installer `abctl`:

```bash
curl -LsfS https://get.airbyte.com | bash
abctl version
```

Installer Airbyte local:

```bash
abctl local install --host "$AIRBYTE_HOST" --port "$AIRBYTE_PORT"
abctl local status
abctl local credentials
```

Enregistré dans `.env`:

```bash
AIRBYTE_CLIENT_ID=...
AIRBYTE_CLIENT_SECRET=...
``` 
avec les valeurs affichées par `abctl local credentials`. 

Préparer le bootstrap versionné:

1. déposer un unique fichier JSON de service account dans `ingestion/airbyte/json_credentials/`
2. renseigner les `spreadsheet_id` dans `ingestion/airbyte/sources/*.json`

Appliquer le bootstrap:

```bash
python3 airbyte/bootstrap.py apply --dry-run
python3 airbyte/bootstrap.py apply
```

### 4.5 Déploiement Docker Compose (dbt, scraping, Prefect)

Démarrer la stack ingestion:

```bash
docker compose up -d
docker compose logs -f prefect-server prefect-worker browserless
```

Comportement attendu:

1. `prefect-server` sert l'UI/API sur `http://localhost:$PREFECT_PORT`
2. `prefect-worker` crée le work pool `ingestion-pool`
3. `prefect-worker` publie les deployments `lancer-ingestion-donnees`, `lancer-scraping-mubi-cnc` et `traiter-les-demandes-ingestion`; le deployment de scraping Allociné seul est désactivé dans `start_worker.sh`
4. `browserless` est utilisé par le scraping Allociné

## 5. Vérifications

Checklist courte:

1. `abctl local status` est OK
2. `docker compose config --quiet` passe
3. `docker compose logs -f prefect-server prefect-worker browserless` ne montre pas d'erreur bloquante
4. l'UI Prefect est accessible: `http://localhost:$PREFECT_PORT`
5. après bootstrap Airbyte, source + destination + connexion sont visibles dans Airbyte
6. `docker compose exec prefect-worker dbt debug --profile ric --project-dir /app/ingestion/dbt` passe
7. `docker compose exec prefect-worker dbt parse --profile ric --project-dir /app/ingestion/dbt` passe

Contrôle SQL minimal après sync Airbyte:

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'raw'
ORDER BY table_name;
```

## 6. Utilisation

### Lancer la pipeline depuis l'UI Prefect

Préparer:

1. Airbyte local actif
2. stack Docker ingestion démarrée
3. bootstrap Airbyte appliqué

Parcours UI:

1. ouvrir `http://localhost:$PREFECT_PORT`
2. aller dans Deployments
3. ouvrir le deployment `lancer-ingestion-donnees`
4. cliquer sur `Run`
5. suivre le run du flow `Lancer l'ingestion complete`

Les étapes visibles dans les logs du même flow run:

1. `Synchroniser les sources` (optionnel)
2. `Preparer les donnees`
3. `Recuperer les donnees Allocine`
4. `Finaliser les donnees` (optionnel)

### Déclencher depuis Metabase

Préparer:

1. table `ops.ingestion_run_requests` créée;
2. grants `INSERT`/`SELECT` donnés au user Metabase;
3. deployment `traiter-les-demandes-ingestion` actif dans Prefect.

La requête d'action Metabase insère une ligne `pending`. Le poller la passe en `processing`, lance `lancer-ingestion-donnees`, puis le flow principal met `success` ou `failed`.

Option CLI (debug):

```bash
docker compose exec prefect-worker python3 /app/ingestion/prefect/flows.py main-ingestion
```

Avec sync Airbyte explicite:

```bash
docker compose exec prefect-worker python3 /app/ingestion/prefect/flows.py main-ingestion \
  --run-airbyte-sync \
  --airbyte-connection-name "src_gsheet_films -> dst_pg_raw"
```

## 7. FAQ

### 7.1 Je change d'environnement (test/prod), que modifier ?

Mettre à jour dans `.env`:

1. `POSTGRES_*`
2. `DBT_USER_POSTGRES_PASSWORD`
3. `SCRAPER_POSTGRES_USER` et `SCRAPER_POSTGRES_PASSWORD`
4. `AIRBYTE_DESTINATION_POSTGRES_PASSWORD`
5. `PREFECT_API_DATABASE_CONNECTION_URL`
6. `PREFECT_AUTH_STRING`
7. `INGESTION_REQUEST_POSTGRES_PASSWORD`

Puis relancer:

```bash
python3 airbyte/bootstrap.py apply
docker compose up -d
```

### 7.2 Airbyte ne démarre pas (port déjà pris)

Choisir un autre port dans `.env` (ex: `AIRBYTE_PORT=8001`) puis relancer `abctl local install`.

### 7.3 Prefect est healthy mais ne crée aucun run planifié

Avec Prefect `3.8.7` et SQLAlchemy `2.1`, le scheduler peut échouer lors de l'insertion des runs avec l'erreur `Can't evaluate bulk DML statement; please supply a bulk_dml decorated function`. Le statut Docker `healthy` vérifie l'API, pas le fonctionnement du scheduler.

L'image ingestion impose `sqlalchemy>=2.0,<2.1` dans `ingestion/prefect/Dockerfile`. Après modification de cette dépendance, reconstruire une seule fois l'image partagée, puis recréer le serveur et le worker sans lancer deux builds concurrents :

```bash
docker compose build prefect-worker
docker compose up -d --no-build --force-recreate prefect-server prefect-worker
docker compose exec prefect-server python -c "import prefect, sqlalchemy; print(prefect.__version__, sqlalchemy.__version__)"
docker compose logs --since 5m prefect-server prefect-worker
```

Vérifier que SQLAlchemy reste en version `2.0.x`, que les erreurs du scheduler ont disparu et que les deployments ayant un schedule actif reçoivent des runs planifiés. Le worker reprend automatiquement les schedules existants; sa procédure de démarrage republie les deployments configurés dans `start_worker.sh`. Ne pas supprimer la base Prefect ni les volumes pour résoudre cette erreur de dépendance.

## 8. Références

1. démarrage rapide Airbyte OSS: [https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart](https://docs.airbyte.com/platform/using-airbyte/getting-started/oss-quickstart)
2. Airbyte `abctl`: [https://docs.airbyte.com/platform/deploying-airbyte/abctl](https://docs.airbyte.com/platform/deploying-airbyte/abctl)
3. destination Postgres Airbyte: [https://docs.airbyte.com/integrations/destinations/postgres](https://docs.airbyte.com/integrations/destinations/postgres)
4. installation dbt Core: [https://docs.getdbt.com/docs/local/install-dbt](https://docs.getdbt.com/docs/local/install-dbt)
5. profils dbt: [https://docs.getdbt.com/docs/local/profiles.yml](https://docs.getdbt.com/docs/local/profiles.yml)
6. setup Postgres dbt: [https://docs.getdbt.com/docs/local/connect-data-platform/postgres-setup](https://docs.getdbt.com/docs/local/connect-data-platform/postgres-setup)
7. serveur Prefect auto-hébergé: [https://docs.prefect.io/](https://docs.prefect.io/)

## 9. Referenced by

- [README.md](../../README.md)
- [ingestion/README.md](../../ingestion/README.md)
