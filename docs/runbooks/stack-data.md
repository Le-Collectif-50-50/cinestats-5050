# Runbook — Stack data (VPS data)

**Resonsable** Nicolas Revel

**Dernière révision:** 2026-10-09

**Status:** active

## Historique du document

| # | Date | Auteur | Observations |
|---|---|---|---|
| 1 | 2026-10-06 | Nicolas Revel | Première version du runbook | 
| 2 | 2026-10-09 | Joel Teixeira | Précision du déploiement depuis main et conservation des fichiers générés et des credentials lors des mises à jour. |

Déploiement de la stack d'ingestion (Prefect, dbt, scrapers, Airbyte) sur le VPS `data` (Canada, 4 vCPU / 8 Go). Le [runbook de setup ingestion](ingestion-runbook-infra-setup-dbt-core-airbyte-remote-postgres.md) décrit le parcours général ; celui-ci consigne les adaptations du VPS. Pour une livraison des changements fusionnés, utiliser explicitement `origin/main` comme indiqué ci-dessous.

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

Pour livrer les changements fusionnés dans `main`, passer explicitement cette référence :

```bash
git fetch origin main
infra/data/deploy-ingestion.sh origin/main
```

La copie conserve aussi `__pycache__/`, `dbt/target/`, `dbt/logs/` et `airbyte/json_credentials/`. Les fichiers générés par Docker peuvent appartenir à root : leur exclusion évite les erreurs de suppression rsync et préserve les credentials Google. Le script copie le code ; reconstruire ensuite l'image et recréer les services concernés selon la section 4. Pour un worker déjà actif, attendre la fin des runs en cours avant son arrêt et son remplacement.

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

## 6. Accès web à Airbyte (SSO Authentik)

Airbyte OSS n'a qu'un mot de passe, sans SSO : il n'est jamais exposé directement. Il est publié sur `https://airbyte.cinestats5050.fr`, derrière Authentik, par ce montage :

```
navigateur → Caddy (VPS data, 80/443, Let's Encrypt) → outpost Authentik (127.0.0.1:9000) → Airbyte (127.0.0.1:8000)
                                                          └─ vérification auprès de auth.cinestats5050.fr
```

Seuls Caddy (80 et 443) et SSH sont joignables depuis Internet : 8000 (Airbyte), 4222 (Prefect) et 9000/9443 (outpost) restent filtrés (vérifié). Airbyte garde son propre mot de passe : deux couches. Le worker Prefect, sur la même machine, appelle l'API d'Airbyte en local et n'est pas concerné par le SSO.

- **Côté Authentik** : blueprint `authentik/blueprints/airbyte.yaml` du dépôt `cinestats-infra` (groupe **Airbyte Admins**, proxy provider, application, outpost distant `airbyte-outpost`). Les personnes autorisées s'ajoutent au groupe dans Authentik (*Directory → Groups*).
- **DNS** : `airbyte.cinestats5050.fr` en A vers l'IP du VPS data, avant de lancer Caddy.
- **Caddy** : `sudo ~/vps/60-caddy.sh airbyte.cinestats5050.fr 9000` (paquet officiel, empreinte SHA-512 vérifiée, ufw 80/443).
- **Outpost** : `infra/data/authentik-outpost/docker-compose.yml`, copié dans `~/cinestats-data/authentik-outpost/`. Son `.env` porte `AUTHENTIK_TOKEN`, à copier depuis Authentik (*Applications → Outposts → airbyte-outpost → View Deployment Info*) et à écrire sur le serveur avec `read -rs`, jamais dans git. Puis `sudo docker compose up -d`.
- **Vérification sans connexion** : `curl -I https://airbyte.cinestats5050.fr/` doit répondre `302` vers `/outpost.goauthentik.io/start`, et il en va de même pour `/api/v1/health`. Suivre les redirections doit arriver sur `auth.cinestats5050.fr`.
- **Accès de secours** : le tunnel SSH reste possible (`ssh -L 8000:localhost:8000 cinestats-data`) et ne passe pas par le SSO.

## 7. Reste à faire

- Airbyte est installé (`abctl` 0.30.4, mode économe : environ 3,3 Go de RAM au repos, il reste environ 3,4 Go pour le worker et Chrome). Reste à le configurer : voir ci-dessous.
- Compte de service Google (Sheets en lecture seule) et URL des 12 feuilles pour `airbyte/bootstrap.py`.
- Corrections côté code de la branche : `sslmode` configurable dans les scrapers (aujourd'hui `disable` en dur), rôle dédié aux scrapers.
- Décision sur le scraping planifié (voir §4).
