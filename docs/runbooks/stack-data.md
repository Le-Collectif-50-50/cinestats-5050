# Runbook — Stack data (VPS data)

Déploiement de la stack d'ingestion (Prefect, dbt, scrapers, Airbyte) sur le VPS `data` (Canada, 4 vCPU / 8 Go). Elle vient de la branche `analytics/dbt_airbyte_setup` : son propre runbook (`docs/runbooks/ingestion-runbook-infra-setup-dbt-core-airbyte-remote-postgres.md` sur cette branche) décrit le parcours, celui-ci en consigne les **écarts** et l'état réel.

Prérequis : `00-base.sh`, `10-wireguard.sh spoke` et `20-docker.sh data` faits sur le VPS (voir `securisation-vps-prod.md`), ainsi que `30-postgres.sh` sur `db`.

## 1. Côté base (VPS `db`) — fait

- `roles.sql` (rejoué par `30-postgres.sh`) crée déjà les schémas `raw`, `staging`, `intermediate`, `fnl`, `ops`, leurs propriétaires et les droits de `airbyte_user`, `dbt_user` et `prefect_user`. C'est l'équivalent du §4.3 du runbook de la branche.
- La table `ops.ingestion_run_requests` n'est pas dans `roles.sql` : elle se crée en `dbt_user` (pour que les droits par défaut des rôles Metabase s'appliquent), puis `roles.sql` se rejoue pour donner ses droits à `prefect_user` :

  ```bash
  sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d cinestats-5050-db < ops-ingestion-table.sql   # infra/data/ops-ingestion-table.sql, copié sur db
  sudo -u postgres psql -X -q -d cinestats-5050-db -v db_name=cinestats-5050-db < ~/vps/sql/roles.sql
  ```

## 2. Copier la stack sur le VPS

Depuis ton poste, à la racine du dépôt :

```bash
git fetch origin
infra/data/deploy-ingestion.sh            # ou : infra/data/deploy-ingestion.sh <ref-git>
```

Le script copie `ingestion/` d'un commit précis (par défaut `origin/analytics/dbt_airbyte_setup`) dans `~/cinestats-data/` et y ajoute `infra/data/docker-compose.override.yml`. Il note le commit dans `~/cinestats-data/DEPLOYED_REF`. Il ne démarre rien et n'écrase jamais le `.env`.

À la première copie, il crée `~/cinestats-data/ingestion/.env` (`600`) depuis `infra/data/.env.example` et **génère `PREFECT_AUTH_STRING` sur le serveur**. Il reste à saisir à la main, dans ce fichier, deux mots de passe pris dans `/root/cinestats-secrets.txt` (VPS `db`) : `DBT_USER_POSTGRES_PASSWORD` et `INGESTION_REQUEST_POSTGRES_PASSWORD` (celui de `prefect_user`).

## 3. Écarts avec la branche analytics

| Sujet | Branche | Ici |
|---|---|---|
| Ports | Prefect publié sur toutes les interfaces, Browserless aussi | Prefect en `127.0.0.1:4222` seulement ; Browserless non publié (le worker l'atteint par le réseau de compose) |
| Base de Prefect | Postgres dédié (`PREFECT_API_DATABASE_CONNECTION_URL`) | SQLite locale dans le volume `prefect-data` : `prefect_user` ne peut pas créer de base sur le Postgres de prod |
| Browserless | 4 CPU / 4 Go, 4 sessions | 1,5 CPU / 2 Go, 2 sessions (le VPS doit aussi porter Airbyte) |
| Compose racine | modifié (`docker-compose*.yaml`) | non repris : la branche y revient à un compte Docker Hub en dur et supprime `INTERNAL_API_URL` |

Surcharge dans `infra/data/docker-compose.override.yml` (fusion vérifiée avec `docker compose config`).

## 4. Construire et démarrer

Sur le VPS, dans `~/cinestats-data/ingestion/` (l'utilisateur admin passe par `sudo docker`) :

```bash
sudo docker compose build prefect-server         # image ric-prefect, partagée avec le worker
sudo docker compose up -d prefect-server         # serveur seul, aucun flux planifié
```

**Ne démarre le worker qu'en connaissance de cause.** `ingestion/prefect/start_worker.sh` (lancé par le worker) enregistre et planifie automatiquement :

- `lancer-scraping-mubi-cnc` : **toutes les 10 minutes**, avec un navigateur Chrome sur Mubi ;
- `traiter-les-demandes-ingestion` : toutes les 5 minutes, interroge `ops.ingestion_run_requests`.

Le premier est un scraping d'un site tiers, planifié sans pause : à valider avant le premier démarrage du worker.

## 5. Accéder à l'interface

Prefect n'est joignable que par tunnel SSH (`AllowTcpForwarding local` sur ce VPS) :

```bash
ssh -L 4222:localhost:4222 cinestats-data      # puis http://localhost:4222
```

Identifiants : la valeur de `PREFECT_AUTH_STRING` du `.env` du serveur (`utilisateur:mot_de_passe`). L'API refuse tout accès sans eux (401) ; `/api/health` et l'interface statique sont publics, sans données.

## 6. Reste à faire

- Airbyte (`abctl local install`) : à installer et à dimensionner avec le worker et Browserless sur 8 Go.
- Compte de service Google (Sheets en lecture seule) et URL des 12 feuilles pour `airbyte/bootstrap.py`.
- Corrections côté code de la branche : `sslmode` configurable dans les scrapers (aujourd'hui `disable` en dur), rôle dédié aux scrapers.
- Décision sur le scraping planifié (voir §4).
