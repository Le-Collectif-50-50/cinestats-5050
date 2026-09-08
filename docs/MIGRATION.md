# Migration vers `Le-Collectif-50-50/cinestats-5050`

Checklist et commandes pour finaliser la migration hors du code. **Rien ici n'est exécuté automatiquement** — copie/colle avec tes propres valeurs.

L'environment GitHub de non-prod s'appelle **`preview`** (existait déjà avant cette migration, avec des secrets/variables datant d'avril — voir §4), et le sous-domaine associé est `preview.cinestats5050.fr`. Il n'y a pas d'environment `staging` : un environment de ce nom a été créé par erreur pendant cette migration puis supprimé une fois la confusion levée.

## 1. Remote git

```bash
git remote rename origin d4g
git remote add origin git@github.com:Le-Collectif-50-50/cinestats-5050.git
git remote -v
```

## 2. Stratégie de branches

`develop` a été abandonnée au profit de `main` comme branche de travail (les PR y sont mergées directement), avec deux branches dédiées au déploiement : `preview` et `production`. Voir `docs/DEPLOYMENT.md` pour le schéma complet.

Ce qui a été fait pendant cette migration :
- `main` avait sa protection de branche avec `lock_branch: true` (branche verrouillée en lecture seule, héritée du repo d'origine) — désactivé, sinon aucune PR n'aurait jamais pu y être mergée.
- `develop` avait un commit que `main` n'avait pas (`ml-image/ml_pipeline_doc.md`) — `main` a été fast-forwardé sur `develop` pour ne rien perdre, puis `develop` a été supprimée.
- `preview` et `production` ont été créées depuis `main` à ce moment-là (donc initialement identiques).
- Le push initial vers ce nouvel org était en retard de 2 commits sur `dataforgoodfr/13_reveler_inegalites_cinema` : le merge `Develop (#216)` (contenu déjà présent via un autre chemin, sans conséquence) et surtout la feature **SEO metadata (PR #217/#218)**, ~1600 lignes sur plusieurs fichiers frontend (`frontend/src/lib/seo.ts`, les pages `about`/`films`/`festivals`/`statistics`), jamais poussée vers le nouvel org. Elle a été récupérée via un merge propre (`main` ← `dataforgoodfr/main`, testé à blanc avant exécution, aucun conflit) — pour ne pas la noyer dans une PR de migration, elle a été intégrée à `main` séparément, puis la branche de migration a été rebasée par-dessus.

## 3. Ordre de bascule

1. Créer l'environment `production` et ses secrets/variables (§4) dans le nouveau repo **avant de faire avancer la branche `production`** — sinon `deploy.yml` échoue dès la première exécution.
2. Compléter l'environment `preview` (§5) — il existe déjà, il manque encore `CERTBOT_EMAIL` et les 3 secrets OVH.
3. Merger les PR sur `main`, puis faire avancer `preview` jusqu'au commit voulu (`git push origin main:preview` en fast-forward, ou une PR `main` → `preview`) → le déploiement preview se déclenche. Vérifier de bout en bout (voir `docs/DEPLOYMENT.md`).
4. Faire avancer `production` de la même façon → les images `latest` sont publiées dans le nouveau namespace, puis le serveur de prod les tire.
5. Rendre les 4 packages GHCR visibles/liés au repo si besoin (`Settings` du package → `Manage Actions access` → lier à `Le-Collectif-50-50/cinestats-5050`).
6. Réactiver Dependabot et Copilot Autofix dans les réglages de sécurité du nouveau repo (ce n'était pas versionné, donc rien ne suit automatiquement).
7. Archiver ou documenter l'état de `dataforgoodfr/13_reveler_inegalites_cinema`.

## 4. Environment `production` — secrets et variables

N'existe pas encore sur le nouveau repo (à créer en premier, avant de faire avancer la branche `production`).

```bash
REPO="Le-Collectif-50-50/cinestats-5050"

gh api repos/$REPO/environments/production -X PUT --input - <<< '{}'

gh secret set SERVER_HOST         --env production --repo $REPO --body "<ip-vps-prod>"
gh secret set SSH_USERNAME        --env production --repo $REPO --body "<user ssh existant>"
gh secret set SSH_PRIVATE_KEY     --env production --repo $REPO --body "$(cat ~/.ssh/<clé-déploiement-prod>)"
gh secret set DATABASE_URL        --env production --repo $REPO --body "postgresql+psycopg://<user>:<pass>@<host>:5432/<db>"
gh secret set METABASE_SITE_URL   --env production --repo $REPO --body "<url>"
gh secret set METABASE_SECRET_KEY --env production --repo $REPO --body "<clé>"
gh secret set METABASE_DASHBOARD_ID --env production --repo $REPO --body "<id>"

gh variable set NEXT_PUBLIC_API_URL --env production --repo $REPO --body "https://api.cinestats5050.fr"
gh variable set ALLOWED_ORIGINS     --env production --repo $REPO --body "https://cinestats5050.fr,https://www.cinestats5050.fr"
gh variable set BACKEND_PORT        --env production --repo $REPO --body "5001"
gh variable set FRONTEND_PORT       --env production --repo $REPO --body "3000"
gh variable set SERVER_PORT         --env production --repo $REPO --body "22022"
```

⚠️ `SERVER_PORT` : les VPS OVH de ce projet sont durcis sur le port SSH **22022** (mot de passe + root désactivés, fail2ban — voir le `~/.ssh/config` local de l'équipe, section "CineStats — 3 VPS-1 OVH"), pas le 22 par défaut. Vérifie que c'est bien le cas pour le serveur qui accueillera la prod avant de poser cette variable.

## 5. Environment `preview` — état actuel

✅ **Complet** : les 12 secrets et 10 variables attendus par `deploy-preview.yml` sont posés.

| Clé | Valeur |
|---|---|
| `SERVER_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY` | clé de déploiement dédiée à la VM preview |
| `SERVER_PORT` (var) | `22022` — port SSH durci, pas le 22 par défaut (voir `~/.ssh/config` local) |
| `POSTGRES_USER` (var) | `postgres` |
| `POSTGRES_DB` (var) | `ric_db` |
| `POSTGRES_PASSWORD` (secret) | généré aléatoirement |
| `DATABASE_URL` (secret) | `postgresql+psycopg://postgres:***@db:5432/ric_db` — pointe sur le Postgres conteneurisé de `docker-compose.preview.yaml`, remplace l'ancienne valeur d'avril |
| `NEXT_PUBLIC_API_URL` (var) | `https://api.preview.cinestats5050.fr` |
| `ALLOWED_ORIGINS` (var) | `https://preview.cinestats5050.fr,https://www.preview.cinestats5050.fr` |
| `DOMAIN`, `API_DOMAIN` (var) | `preview.cinestats5050.fr` / `api.preview.cinestats5050.fr` |
| `RUN_SEED` (var) | `true` |
| `BACKEND_PORT`, `FRONTEND_PORT` (var) | `5001` / `3000` — déjà présents depuis avril, inchangés |
| `METABASE_SITE_URL`, `METABASE_SECRET_KEY`, `METABASE_DASHBOARD_ID` | déjà présents depuis avril, réutilisés tel quel |
| `CERTBOT_EMAIL` | posé |
| `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY` | posés |

Reste hors GitHub : DNS `preview.cinestats5050.fr` / `api.preview.cinestats5050.fr` pointés vers la VM (voir §7), et la VM elle-même provisionnée avec `scripts/provision-preview.sh`.

`DATABASE_URL` utilise le préfixe `postgresql+psycopg://` (et non `postgresql://`) : le projet n'a que `psycopg` v3 d'installé (`poetry.lock`), pas `psycopg2` — SQLAlchemy cherche `psycopg2` par défaut avec le préfixe nu et le service `migrate` planterait au démarrage. `postgres` / `ric_db` reprennent la convention déjà utilisée dans `docker-compose.yaml` (dev) et `.env` local.

## 6. Credentials OVH pour le DNS-01

1. Aller sur https://eu.api.ovh.com/createToken/ (adapter le TLD `.ca`/`.us` selon la zone OVH réelle du domaine).
2. Renseigner :
   - **Application name** : `cinestats5050-preview-certbot`
   - **Rights** : `GET`, `POST`, `DELETE` sur le chemin `/domain/zone/*`
   - **Validity** : illimitée (le token est utilisé en continu par le renouvellement automatique)
3. Récupérer les 3 valeurs retournées : `Application Key`, `Application Secret`, `Consumer Key` — ce sont respectivement `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY` du §5.
4. ⚠️ Ces clés donnent le droit d'écrire dans la zone DNS du domaine — à traiter comme un secret sensible, jamais commité.

## 7. DNS et machine preview

- Créer les enregistrements DNS chez OVH : `preview.cinestats5050.fr` et `api.preview.cinestats5050.fr` → A/AAAA vers l'IP de la VM preview.
- Provisionner la VM avec `scripts/provision-preview.sh` (Docker, arborescence `~/cinestats5050-preview`, clé SSH de déploiement autorisée).
- Aucune création manuelle de certificat n'est nécessaire : `certbot/entrypoint-dns.sh` l'émet automatiquement au premier démarrage du conteneur `certbot`.
