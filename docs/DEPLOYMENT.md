# Déploiement

## Stratégie de branches

`main` est la branche de travail : les PR y sont mergées après review (1 approbation requise). `preview` et `production` sont des branches de déploiement dédiées, sans historique divergent — on y fait remonter (fast-forward ou merge) le contenu de `main` quand on veut déclencher un déploiement, jamais de travail direct dessus.

```
feature/xxx ──┐
              ├──► main ──► preview ──► production
feature/yyy ──┘      (PR)   (promotion) (promotion)
```

## Environnements

Le projet a deux environnements, chacun sur sa propre machine, déclenchés par un push sur une branche donnée :

| Environnement | Branche | Workflow | Environment GitHub | Domaine |
|---|---|---|---|---|
| Preview | `preview` | `.github/workflows/deploy-preview.yml` | `preview` | `preview.cinestats5050.fr` |
| Production | `production` | `.github/workflows/deploy.yml` | `production` | `cinestats5050.fr` |

Les deux peuvent aussi être déclenchés manuellement (`workflow_dispatch`).

Pour déployer : faire avancer la branche `preview` (ou `production`) jusqu'au commit de `main` qu'on veut déployer — par exemple `git push origin main:preview` pour un fast-forward, ou une PR `main` → `preview` si l'historique a divergé.

## Flux commun

1. **Build** : 4 images (backend, frontend, nginx, certbot) sont construites et poussées sur `ghcr.io/<owner>/<repo>/<image>` (le nom est dérivé de `github.repository`, minusculisé par `docker/metadata-action`).
2. **Deploy** : `docker-compose.<env>.yaml`, `nginx/` et `certbot/` sont copiés en SSH sur le serveur, un `.env` est régénéré à partir des secrets/variables de l'environment GitHub, puis `docker compose pull && up -d`.

Le `.env` du serveur est **entièrement régénéré à chaque déploiement** — jamais édité à la main, jamais persistant entre deux runs.

## Production

- Images taguées `latest` + `sha-<commit>`.
- **3 VPS OVH** durcis par `infra/vps/` (procédure complète : [`docs/runbooks/securisation-vps-prod.md`](runbooks/securisation-vps-prod.md)) :

  | VPS | Rôle | Joignable depuis Internet |
  |---|---|---|
  | `app` | nginx + frontend + backend (ce workflow) | 80, 443, SSH 22022 |
  | `db` | PostgreSQL 16 natif, sauvegardé par pgBackRest | SSH 22022, WireGuard (UDP 51820, IP des pairs seulement) |
  | `data` (Canada) | Airbyte, Prefect, dbt, scrapers | SSH 22022 |

  `app` et `data` parlent à `db` par un tunnel WireGuard (`10.50.0.0/24`, `db` = `10.50.0.1`) ; Postgres n'écoute pas sur l'IP publique.
- Déployée sous `~/cinestats5050` du compte `deploy` du VPS `app` (groupe `docker`, sans sudo).
- `docker compose down` puis `up -d` → **coupure de service à chaque déploiement**.
- TLS : HTTP-01 (webroot), boucle `certbot renew` toutes les 12h. **Le certificat initial doit être créé à la main** en SSH sur le serveur (`certbot certonly --webroot ...`) — `certbot/entrypoint.sh` ne fait que le renouvellement.
- Le backend se connecte avec le rôle **`app_ro`, en lecture seule** (l'API n'a que des routes GET) : `DATABASE_URL=postgresql+psycopg://app_ro:***@10.50.0.1:5432/cinestats-5050-db?sslmode=require`.
- Aucune migration Alembic automatique : à jouer à la main depuis le VPS `app` avec le rôle **`app_migrator`**, seul à pouvoir modifier le schéma. Son mot de passe vient du gestionnaire de mots de passe et n'est jamais stocké sur le serveur :

  ```bash
  sudo -iu deploy
  cd ~/cinestats5050
  read -rs MIGRATOR_PW   # colle le mot de passe d'app_migrator, rien ne s'affiche
  export DATABASE_URL="postgresql+psycopg://app_migrator:$MIGRATOR_PW@10.50.0.1:5432/cinestats-5050-db?sslmode=require"
  docker compose run --rm -e DATABASE_URL backend alembic -c database/alembic.ini upgrade head
  exit                   # la session deploy et ses variables disparaissent
  ```

### Secrets (environment `production`)
`SERVER_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`, `DATABASE_URL`, `METABASE_SITE_URL`, `METABASE_SECRET_KEY`, `METABASE_DASHBOARD_ID`.

### Variables (environment `production`)
`NEXT_PUBLIC_API_URL`, `ALLOWED_ORIGINS`, `BACKEND_PORT`, `FRONTEND_PORT`, `SERVER_PORT` (`22022` : port SSH des VPS durcis par `infra/vps/00-base.sh`, pas le 22 par défaut).

`SSH_USERNAME` vaut `deploy` et `SSH_PRIVATE_KEY` est la clé privée dédiée dont la clé publique a été passée à `infra/vps/20-docker.sh app`. L'environment `production` doit exiger un reviewer et n'autoriser que la branche `production` : un accès à ce secret équivaut à un accès root au VPS `app`.

## Preview

- Images taguées `preview` + `sha-<commit>`.
- Déployée sous `~/cinestats5050-preview` sur une **machine dédiée**, distincte du serveur de prod.
- Pas de `docker compose down` avant `up -d --remove-orphans` : les conteneurs changés sont recréés en place, ce qui limite l'interruption.
- Base de données : **Postgres conteneurisé** dans `docker-compose.preview.yaml` (service `db`, volume `preview-db-data`), pas de dépendance à une base externe.
- **Migrations Alembic automatiques** : un service one-shot `migrate` joue `alembic -c database/alembic.ini upgrade head` avant que `backend` ne démarre (`depends_on: migrate: condition: service_completed_successfully`). C'est le but même de la preview : vérifier qu'une migration passe avant de la rejouer à la main en prod.
- **Seed automatique**, piloté par la variable `RUN_SEED` (`true`/`false`) — les 5 scripts de `database/seed/` n'étant pas garantis idempotents, mets `RUN_SEED=false` si tu vois des doublons apparaître après un merge.
- **Umami désactivé** : le build ne reçoit pas `NEXT_PUBLIC_UMAMI_WEBSITE_ID`, donc le script n'est pas injecté (voir `frontend/src/app/layout.tsx`) — les visites de test sur preview ne polluent pas les statistiques de prod.
- **Metabase réutilisé** : mêmes identifiants que la prod (même instance Metabase).
- TLS : **DNS-01 via l'API OVH** (`certbot/dns-ovh`, `certbot/entrypoint-dns.sh`). Contrairement à la prod, **le certificat initial est créé automatiquement** au premier démarrage du conteneur — rien à faire à la main sur le serveur.

### Secrets (environment `preview`)
`SERVER_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`, `DATABASE_URL` (interne, ex. `postgresql+psycopg://postgres:***@db:5432/ric_db` — le préfixe `+psycopg` est obligatoire, le projet n'a que psycopg v3 d'installé, pas psycopg2), `POSTGRES_PASSWORD`, `METABASE_SITE_URL`, `METABASE_SECRET_KEY`, `METABASE_DASHBOARD_ID`, `CERTBOT_EMAIL`, `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`.

### Variables (environment `preview`)
`NEXT_PUBLIC_API_URL`, `ALLOWED_ORIGINS`, `BACKEND_PORT`, `FRONTEND_PORT`, `SERVER_PORT` (`22022`), `POSTGRES_USER`, `POSTGRES_DB`, `RUN_SEED`, `DOMAIN` (`preview.cinestats5050.fr`), `API_DOMAIN` (`api.preview.cinestats5050.fr`).

Voir `docs/MIGRATION.md` pour les commandes `gh` exactes et la procédure OVH.

## Rollback

**Production** : redéployer une image précédente en repointant manuellement les 4 services sur un tag `sha-<commit>` connu (`docker compose pull && up -d` après avoir édité `docker-compose.prod.yaml` ou en passant `IMAGE_PREFIX`/tag explicitement), puis rejouer `deploy.yml` via `workflow_dispatch` une fois le correctif poussé sur `production`.

**Preview** : aucun enjeu de service — relancer `workflow_dispatch` sur `deploy-preview.yml`, ou `docker compose down -v && up -d` sur le serveur pour repartir d'une base vide (les migrations et le seed se rejouent automatiquement).

## Provisioning d'une nouvelle machine

- **Production** (VPS `app`, `db`, `data`) : scripts `infra/vps/`, à dérouler dans l'ordre de [`docs/runbooks/securisation-vps-prod.md`](runbooks/securisation-vps-prod.md).
- **Preview** : `scripts/provision-preview.sh` pour l'amorçage d'une VM preview vierge (Docker, arborescence, clé SSH de déploiement).
