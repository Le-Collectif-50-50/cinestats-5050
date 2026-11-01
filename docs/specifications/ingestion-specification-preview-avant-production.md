# Spécification — Lancer l'ingestion sur la preview avant la production

**Owner:** Nicolas Revel

**Dernière révision:** 2026-11-01

**Status:** brouillon

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-31 | Nicolas Revel | Proposition initiale : la stack data actuelle alimente aussi la base de l'environnement preview, pour vérifier les changements dans l'app `preview.cinestats5050.fr` avant de les publier en production. À valider par Joel Teixeira avant implémentation. |
| 2 | 2026-11-01 | Nicolas Revel | Prérequis retenu : le backend lit les tables `fnl_*` au lieu des tables `ric_*` couvertes par la pipeline. Ajout de la stratégie d'identifiant film (URL publiques), du lien avec les tables restées en `ric_*` et des droits de `app_ro`. |

## 1. Objectif

Avant chaque mise à jour de données en production, lancer la même pipeline (`airbyte sync → dbt phase 1 → scraping → dbt phase 2`) sur la **base de l'environnement preview**. On vérifie ensuite le résultat **dans l'app preview**, puis on relance sur la production.

Le besoin : voir l'effet d'une correction du Google Sheet `Modification data` ou d'un changement de modèle dbt sur les pages réelles du site, et pas seulement dans des tables.

Principe : **une seule stack data** (le VPS `data` actuel), **deux bases cibles**, choisies au lancement de chaque run.

## 2. État actuel (vérifié dans le code au 2026-10-31)

| Élément | Constat | Source |
| --- | --- | --- |
| Tables lues par l'app | Le backend lit uniquement les tables `ric_*` (`ric_films`, `ric_credit_holders`, `ric_film_credits`…), créées par Alembic et remplies par les seeds de `database/seed/`. 14 repositories, 3 use cases, 3 routes GET (`/films/{film_id}` avec un identifiant entier, `/search`, `/festivals/{festival_id}`). Le rôle `app_ro` ne lit que le schéma `public`. | [database/models/](../../database/models/), [backend/](../../backend/), [roles.sql](../../infra/vps/sql/roles.sql) |
| URL publiques | Les pages film sont `/films/<ric_films.id>` (lien depuis la recherche et les pages festival). | [frontend/src/app/films/[slug]/page.tsx](../../frontend/src/app/films/[slug]/page.tsx), [Navbar.tsx](../../frontend/src/components/atoms/Navbar.tsx) |
| Tables produites par la pipeline | dbt publie `fnl.fnl_films`, `fnl_credit_holders`, `fnl_film_credits`, `fnl_film_genre`, `fnl_genre`, `fnl_role`, `fnl_film_country_budget_allocation`. **Le backend ne lit aucune de ces tables.** | [ingestion/dbt/models/fnl/](../../ingestion/dbt/models/fnl/) |
| Base cible de la stack data | Une seule base, `cinestats-5050-db` sur le VPS `db`, jointe par le tunnel WireGuard. Un seul `.env`. | [infra/data/.env.example](../../infra/data/.env.example) |
| Base preview | Postgres conteneurisé (service `db`) sur la machine preview, **sans port publié**, rempli par Alembic et le seed (`RUN_SEED`). Pas de schémas `raw`/`staging`/`intermediate`/`fnl`/`ops`, pas de rôles d'ingestion, pas de TLS. | [docker-compose.preview.yaml](../../docker-compose.preview.yaml), [DEPLOYMENT.md](../DEPLOYMENT.md#preview) |
| Réseau | WireGuard en étoile centré sur `db` : `app` et `data` ne voient que `db`. La machine preview n'en fait pas partie. | [infra/vps/10-wireguard.sh](../../infra/vps/10-wireguard.sh) |
| Choix de la base dans les outils | dbt : une seule cible `default`. Scraper Allociné : placeholders `${POSTGRES_HOST}`… dans un fichier de config passé en paramètre (`config_path`). Airbyte : une destination par connexion, choisie par nom. | [profiles.yml](../../ingestion/dbt/profiles/profiles.yml), [config.json](../../ingestion/scraping/allocine/config.json), [flows.py](../../ingestion/prefect/flows.py) |
| Déclenchement Metabase | L'action SQL écrit dans `ops.ingestion_run_requests` (base de prod) ; le poller lance `lancer-ingestion-donnees`. | [metabase-trigger-ingestion.sql](../../infra/data/metabase-trigger-ingestion.sql) |

**Conséquence principale :** brancher la pipeline sur la base preview ne change pas l'app preview tant que le backend lit `ric_*`. Faire lire `fnl` au backend (§4.1) est un **prérequis**. C'est la phase 4 « Backend / Exposition » déjà prévue par la [spécification Airbyte/dbt](ingestion-specification-airbyte-dbt-mises-a-jour-donnees.md#114-phase-4---backend--exposition). La preview sert alors de répétition, comme pour les migrations Alembic : le nouveau backend est déployé en preview sur des données `fnl` produites par la pipeline, puis en production.

## 3. Périmètre

Couvert :

1. accès réseau privé du VPS `data` à la base preview ;
2. provisionnement de la base preview pour l'ingestion (schémas, rôles) ;
3. choix de la base cible au lancement d'un run (Prefect, CLI, Metabase) ;
4. lecture des tables `fnl_*` par le backend, d'abord en preview ;
5. parcours « preview, vérification dans l'app, production ».

Non couvert :

1. les données sans équivalent `fnl` : affiches, bandes-annonces et prédictions ML (`ric_posters`, `ric_trailers`, `ric_*_characters`), festivals et récompenses (`ric_festivals`, `ric_festival_awards`, `ric_award_nominations`). Elles restent dans `ric_*`, alimentées par les seeds, jusqu'à ce que la pipeline les produise (`int_mubi_*` existe déjà, sans modèle `fnl`) ;
2. un second VPS data ou une seconde stack Prefect.

## 4. Conception

### 4.1 Prérequis — le backend lit `fnl`

Le backend lit les tables `fnl_*` pour tout ce que la pipeline produit, et garde `ric_*` pour le reste :

| Données | Lues dans |
| --- | --- |
| Films, crédits, personnes, rôles, genres, budgets et pays | `fnl.fnl_films`, `fnl_film_credits`, `fnl_credit_holders`, `fnl_role`, `fnl_genre`, `fnl_film_genre`, `fnl_film_country_budget_allocation` |
| Affiches, bandes-annonces, prédictions ML, festivals, récompenses | `ric_*` inchangées, tant qu'il n'existe pas de modèle `fnl` équivalent |

Points à traiter :

1. **Modèles et repositories.** De nouveaux modèles SQLAlchemy en lecture seule sur le schéma `fnl` (`__table_args__ = {"schema": "fnl"}`), sans migration Alembic : dbt possède ces tables. Les repositories concernés (`film`, `film_credit`, `credit_holder`, `role`, `genre`, `country`, `film_country_budget_allocation`) changent de modèle, et les entités exposées par l'API gardent leur forme, pour que le frontend ne change pas.
2. **Correspondance des colonnes.** Les noms et certains types diffèrent : `original_name` / `movie_name`, `visa_number` / `cnc_visa`, `duration_minutes` / `duration_mn`, `parity_bonus` / `has_parity_bonus`, `cnc_agrement_year` / `cnc_agreement_year`, `genre_categories` / `genre_category`, `asr` (texte) / `has_asr` (booléen), `cnc_rank` (entier) / `filmography_rank` (texte). Le mapping se fait dans les repositories, ou dans une vue dbt d'exposition (par exemple `fnl.api_films`) qui renomme déjà les colonnes. Le choix se fait au lot 4, avec Joel Teixeira.
3. **Identifiant film et URL publiques.** Les pages sont `/films/<ric_films.id>`, alors que `fnl_films.film_id` est un UUID dérivé du visa. Options :
   - garder un identifiant entier stable : une table de correspondance `visa → id` publiée par dbt et initialisée depuis `ric_films`, qui conserve les URL existantes ;
   - ou passer aux URL en UUID (ou en slug) et rediriger les anciennes URL `/films/<entier>` grâce à la même correspondance.

   La première option est la plus sûre : aucune URL partagée ni aucun lien indexé ne casse.
4. **Lien avec les tables restées en `ric_*`.** Les affiches, bandes-annonces et nominations référencent `ric_films.id`. Le backend les rattache aux films `fnl` par la correspondance du point 3, ou par le visa (`ric_films.visa_number = fnl_films.cnc_visa`). Les films présents dans `fnl` mais absents de `ric_films` n'ont alors ni affiche ni bande-annonce : l'API doit le tolérer.
5. **Droits.** `app_ro` doit lire `fnl` : `GRANT USAGE ON SCHEMA fnl TO app_ro;`, `GRANT SELECT ON ALL TABLES IN SCHEMA fnl TO app_ro;` et `ALTER DEFAULT PRIVILEGES FOR ROLE dbt_user IN SCHEMA fnl GRANT SELECT ON TABLES TO app_ro;` dans [roles.sql](../../infra/vps/sql/roles.sql). dbt recrée les tables à chaque run, d'où les droits par défaut.
6. **Disponibilité pendant un run.** dbt remplace chaque table `fnl` en fin de construction. Une requête API peut lire un état intermédiaire entre deux tables du même run : risque faible, mais à vérifier en preview.
7. **Bascule pilotée par une variable.** `preview` et `production` sont toutes deux promues depuis `main` ([DEPLOYMENT.md](../DEPLOYMENT.md#stratégie-de-branches)). Un backend qui lit `fnl` sans condition partirait en production à la prochaine promotion d'un autre correctif, même si `fnl` n'y est pas encore prêt. Proposition : une variable d'environment GitHub `DATA_SOURCE` (`ric` ou `fnl`, `ric` par défaut), lue par les repositories. On la passe à `fnl` en preview au lot 4, puis en production au lot 6.
8. **Tests.** Tests API de non-régression sur les trois routes : mêmes réponses pour un échantillon de films avant et après la bascule, en preview.

### 4.2 Réseau — rendre la base preview joignable depuis le VPS `data` uniquement

La base preview ne doit pas être joignable depuis Internet. Proposition : un **tunnel WireGuard point à point** entre `data` et `preview`, séparé de l'étoile de production :

1. une seconde interface (`wg-preview`) sur `data` et sur `preview`, avec un sous-réseau privé distinct de celui de la production ;
2. sur `preview`, ufw autorise le port WireGuard uniquement depuis l'IP publique de `data`, et le port Postgres uniquement sur l'interface `wg-preview` ;
3. dans `docker-compose.preview.yaml`, publier le service `db` **sur l'adresse WireGuard de `preview` seulement**, avec la variable `PREVIEW_DB_BIND_ADDRESS` dans l'environment GitHub `preview` :

   ```yaml
     db:
       ports:
         - "${PREVIEW_DB_BIND_ADDRESS:?adresse WireGuard de preview}:5432:5432"
   ```

   Attention : Docker écrit ses propres règles iptables, qui passent avant ufw. C'est l'adresse de liaison qui protège, pas ufw : ne jamais publier sur `0.0.0.0`.

4. Le trafic est chiffré par WireGuard, et le conteneur Postgres n'a pas de TLS : `sslmode=disable` sur ce lien uniquement. La production garde `require`.

Alternative plus légère : un tunnel SSH permanent (`autossh`) depuis `data`, avec le port publié sur `127.0.0.1` de la machine preview. Pas de nouvelle interface, mais un processus de plus à superviser.

Le script d'ajout du tunnel s'inspire de [10-wireguard.sh](../../infra/vps/10-wireguard.sh). Il doit rester distinct, pour ne pas modifier l'étoile de production.

### 4.3 Base preview — schémas et rôles

À faire une fois, puis après chaque `docker compose down -v` (qui efface la base) :

1. créer les rôles `airbyte_user`, `dbt_user`, `scraper_user` dans le conteneur, avec des mots de passe **propres à la preview**, stockés dans l'environment GitHub `preview` et dans le `.env` du VPS `data` ;
2. rejouer [roles.sql](../../infra/vps/sql/roles.sql) avec `psql -v db_name=<base preview>` pour créer les schémas `raw`, `staging`, `intermediate`, `fnl`, `ops` et leurs droits. Les rôles absents de la preview (`app_migrator`, `app_ro`, `metabase_*`, `prefect_user`) doivent être créés vides ou retirés de cette exécution, à trancher pendant l'implémentation ;
3. option : automatiser 1 et 2 dans le service one-shot `migrate` de `docker-compose.preview.yaml`, après Alembic.

Données de départ : copier une fois `raw.allocine_data` de la production vers la preview (dump/restore du seul tableau). Sinon, le premier scraping en preview interroge Allociné pour tous les films.

Les seeds restent utiles en preview pour les tables gardées en `ric_*` (affiches, bandes-annonces, festivals) et pour `ric_films`, qui initialise la correspondance d'identifiants du §4.1. Le backend preview se connecte avec le superutilisateur du conteneur (`DATABASE_URL` interne) : les droits `app_ro` du §4.1 ne concernent que la production.

### 4.4 Choisir la base cible au lancement

Un paramètre unique, `target: Literal["production", "preview"] = "production"`, ajouté à `main_ingestion_flow` et au CLI, détermine les quatre réglages :

| Outil | Production | Preview |
| --- | --- | --- |
| dbt | `--target default` | `--target preview` : nouvelle sortie dans `profiles.yml`, lue depuis `PREVIEW_POSTGRES_HOST`, `PREVIEW_POSTGRES_PORT`, `PREVIEW_POSTGRES_DB`, `PREVIEW_DBT_USER_POSTGRES_PASSWORD`, `PREVIEW_POSTGRES_SSLMODE` |
| Scraper Allociné | `scraping/allocine/config.json` | `scraping/allocine/config.preview.json`, mêmes clés avec les variables `PREVIEW_*` |
| Airbyte | `INGESTION_REQUEST_AIRBYTE_CONNECTION_NAMES` | `PREVIEW_AIRBYTE_CONNECTION_NAMES` : connexions vers une destination `dst_pg_raw_preview`, créées par le [bootstrap Airbyte](../../ingestion/airbyte/README.md) avec des manifests paramétrés par cible |

Les variables `PREVIEW_*` s'ajoutent au `.env` du VPS `data` ([infra/data/.env.example](../../infra/data/.env.example)) sans valeur dans git. La file `ops.ingestion_run_requests` et Prefect restent en production : seules les données changent de base.

Ajouter `--concurrency-limit 1` au deployment `lancer-ingestion-donnees` dans [start_worker.sh](../../ingestion/prefect/start_worker.sh). Aujourd'hui, seul le poller est limité, et il n'attend pas la fin du run qu'il déclenche : un run preview et un run production pourraient s'exécuter en même temps.

### 4.5 Metabase

1. Migration additive de [ops-ingestion-table.sql](../../infra/data/ops-ingestion-table.sql) :

   ```sql
   ALTER TABLE ops.ingestion_run_requests
     ADD COLUMN IF NOT EXISTS target TEXT NOT NULL DEFAULT 'production'
     CHECK (target IN ('production', 'preview'));
   ```

2. Deux actions dans Metabase :
   - « Mettre à jour la preview » : `target = 'preview'`, `dedupe_key = CONCAT('metabase:preview:', CURRENT_DATE::TEXT)` ;
   - « Publier en production » : l'action actuelle, avec `target = 'production'` explicite.
3. Le poller lit `target` dans la ligne claimée et le passe au flow (`_build_request_parameters`).

## 5. Parcours opérateur

1. Mettre à jour le Google Sheet `Modification data`.
2. Dans Metabase, cliquer sur **Mettre à jour la preview**. Le run synchronise le Sheet vers la base preview, puis construit dbt dans la base preview. L'app preview lit directement les nouvelles tables `fnl`.
3. Vérifier les pages concernées sur `preview.cinestats5050.fr`.
4. Si c'est conforme, cliquer sur **Publier en production**. Sinon, corriger le Sheet et revenir à l'étape 2.

Comme les deux runs relisent le Sheet, une modification faite entre l'étape 2 et l'étape 4 serait publiée sans avoir été vérifiée. Consigne : ne pas modifier le Sheet entre les deux runs.

## 6. Plan de mise en œuvre

Une PR par lot. Les lots 1 à 3 ne changent rien en production.

| Lot | Contenu | Vérifications |
| --- | --- | --- |
| 1 | Tunnel `data` ↔ `preview` et port Postgres publié sur l'adresse du tunnel uniquement. | Depuis `data` : `pg_isready` vers la base preview. Depuis l'extérieur : port Postgres de la machine preview fermé (`nc -vz`). |
| 2 | Rôles et schémas d'ingestion dans la base preview, copie initiale de `raw.allocine_data`. | Connexion de chaque rôle depuis `data` ; `has_schema_privilege` sur les schémas attendus. |
| 3 | Paramètre `target` : sortie dbt `preview`, config scraper, connexions Airbyte preview, limite de concurrence. Run manuel Prefect avec `target=preview`. | Tables `fnl_*` remplies dans la base preview ; aucune écriture en production (horodatage et volumétrie de `fnl` en prod inchangés). |
| 4 | Backend sur `fnl` (§4.1) : modèles, repositories, correspondance d'identifiants, variable `DATA_SOURCE`. Activé en preview uniquement (`DATA_SOURCE=fnl`), `ric` en production. | URL `/films/<id>` existantes toujours valides ; affiches et bandes-annonces toujours liées ; tests API de non-régression contre la base preview ; pages vérifiées sur `preview.cinestats5050.fr`. |
| 5 | Colonne `target`, poller, deux actions Metabase. | Demande `preview` traitée en `success`, base de prod inchangée. |
| 6 | Bascule en production : droits `app_ro` sur `fnl`, run d'ingestion production, puis `DATA_SOURCE=fnl` dans l'environment `production` et redéploiement. | `fnl` en production à jour avant la bascule ; tests API sur la prod ; retour arrière par `DATA_SOURCE=ric`, car `ric_*` reste intact. |
| 7 | Documentation : [README ingestion](../../ingestion/README.md), [runbook stack data](../runbooks/stack-data.md), [DEPLOYMENT.md](../DEPLOYMENT.md). | Liens et commandes relus. |

## 7. Risques et limites

1. **Chaque run de production modifie directement le site.** Une fois le backend sur `fnl`, un run dbt en erreur ou des données fausses sont visibles tout de suite. Mesures : le passage par la preview (objet de ce document), des tests dbt bloquants sur `fnl` et, en cas de problème, le retour à `DATA_SOURCE=ric` (§4.1, point 7), les tables `ric_*` restant intactes.
2. **La preview peut repartir de zéro.** Un `docker compose down -v` efface rôles, schémas et données d'ingestion : il faut alors rejouer le lot 2. À documenter dans [DEPLOYMENT.md](../DEPLOYMENT.md#rollback).
3. **Ressources du VPS `data`.** Les runs preview s'ajoutent aux runs de production sur un VPS déjà serré (Airbyte, Chrome). La limite de concurrence les sérialise ; à surveiller.
4. **Scraping en double.** Chaque base a son propre `raw.allocine_data` : un nouveau film est scrapé deux fois, une fois par base. Le volume est faible si l'on fait la copie initiale du §4.3.
5. **Écart de code.** Les deux cibles utilisent le code déployé sur le VPS `data`. Pour tester un modèle dbt modifié avant son déploiement, voir la question ouverte n° 4.
6. **Secrets supplémentaires.** Mots de passe des rôles preview et clé WireGuard : hors git, dans l'environment GitHub `preview` et le `.env` du VPS `data`.

## 8. Alternatives écartées

1. **Prévisualisation dans la base de production**, dans des schémas suffixés `_preview` : aucune ouverture réseau, mais rien n'est visible dans l'app. Écartée, car l'objectif est de vérifier les changements dans l'app preview.
2. **Copier `fnl` vers `ric_*`** après chaque run, pour ne pas modifier le backend : il faudrait maintenir à la fois les tables `ric_*` et une étape de copie qui réécrit les tables de l'app. Écartée, au profit de la phase 4 déjà prévue (backend sur la couche finale).

## 9. Questions ouvertes

1. Joel Teixeira : mapping des colonnes dans les repositories ou dans des vues dbt d'exposition (`fnl.api_*`) ? Identifiant entier stable ou URL en UUID avec redirection (§4.1, point 3) ?
2. Tunnel WireGuard dédié ou tunnel SSH ?
3. Les rôles et schémas de la preview doivent-ils être recréés automatiquement par le service `migrate` ?
4. Faut-il, plus tard, pouvoir lancer en preview un code non encore déployé (second répertoire de code sur le VPS `data`) ?
5. Faut-il bloquer « Publier en production » sans run preview réussi le même jour ?

## Références

- [Spécification Airbyte/dbt](ingestion-specification-airbyte-dbt-mises-a-jour-donnees.md)
- [Plan du système de déclenchement](ingestion-trigger-system-plan.md)
- [Architecture ingestion](../architecture/ingestion-architecture-airbyte-dbt-prefect-scraping.md)
- [README ingestion](../../ingestion/README.md)
- [Runbook stack data](../runbooks/stack-data.md)
- [Déploiement](../DEPLOYMENT.md)
