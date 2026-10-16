# Scraping Allocine

## Metadata du document

**Owner:** Joel Teixeira

**Dernière révision:** 2026-10-15

**Status:** actif

## Historique du document

| #   | Date       | Auteur        | Observations           |
| --- | ---------- | ------------- | ---------------------- |
| 1   | 2026-05-07 | Joel Teixeira | Initial implementation |
| 2   | 2026-05-26 | Joel Teixeira | Alignement avec le flow Prefect actuel et la phase dbt post-scraping exécutable |
| 3   | 2026-10-06 | Joel Teixeira | Compte Postgres scraper dédié et SSL configuré par environnement. Alignement des modèles dbt post-scraping sur le code actuel |
| 4   | 2026-10-09 | Joel Teixeira | Correction du passage de configuration dans la commande `read`, qui échouait avec un `TypeError` avant le scraping |
| 5   | 2026-10-09 | Joel Teixeira | Copie des helpers de date et durée dans ingestion pour démarrer sans package backend |
| 6 | 2026-10-11 | Joel Teixeira | Sélection dbt post-scraping incluant les modèles intermédiaires et finaux et leurs dépendances |
| 7 | 2026-10-15 | Data Team DataForGood | Persistance des URL d’affiche, migration additive, backfill local journalisé, export/import SQL ciblé et tests PostgreSQL isolés. |

Job de scraping standalone pour le sous-graphe cible `Scraping flow`.

Objectif: remplacer le handoff CSV historique dans `database/data/allocine/` par un flux brut stocké en base nommé `allocine_data`.

## Ce que fait la source

1. Lit actuellement les films candidats depuis `raw.id_matching`.
2. Crée automatiquement la table mémoire de sortie si elle n'existe pas encore.
3. Lit les lignes déjà réussies dans `raw.allocine_data` pour ignorer les enregistrements déjà traités.
4. Utilise le parseur HTML Allociné et la session navigateur Playwright du package ingestion :
   - `ingestion/scraping/allocine/allocine_scraper.py`
   - `ingestion/scraping/browser.py`
5. Ecrit un enregistrement normalisé par film dans la table `allocine_data`.

## Dépendances du runtime

Le connecteur utilise `ingestion/scraping/date_utils.py` pour convertir les dates françaises et les durées. Ce module contient une copie de `parse_release_date` et `parse_duration` du backend, avec le même comportement. Les fonctions originales restent dans le backend pour ses consommateurs.

Le démarrage du scraper ne nécessite pas le package `backend`. La dépendance `dateparser` est déjà déclarée dans `requirements.txt` et installée dans l'image Prefect. Toute évolution de ces conversions doit tenir compte des deux copies.

Pour vérifier les conversions et le démarrage CLI avec une copie isolée du package ingestion, après installation des dépendances du scraper et de `pytest`, depuis la racine du dépôt :

```bash
python3 -m pytest -q tests/ingestion/test_allocine_date_utils.py
```

Ce test lance `spec` sans backend, sans connexion PostgreSQL et sans démarrer de navigateur.

## Contrat de sortie

Champs principaux:

1. identité source: `source_record_id`, `visa_number`, `original_name`, `cnc_agrement_year`
2. métadonnées Allociné: `allocine_id`, `allocine_title`, `allocine_url`, `allocine_visa_number`
3. charge utile enrichie: `release_date`, `duration_minutes`, `genres`, `poster_url`, `trailer_url`, `direction`, `casting`, `screenwriters`, `production`, `technical_team`, `soundtrack`, `distribution`, `companies`
4. observabilité: `run_id`, `extracted_at`, `search_url`, `source_url`, `scrape_status`, `error_message`, `record_hash`

## Configuration

Exemple minimal:

```json
{
  "postgres_host": "${POSTGRES_HOST:-localhost}",
  "postgres_port": "${POSTGRES_PORT:-5432}",
  "postgres_db": "${POSTGRES_DB:-reveler_inegalites_cinema}",
  "postgres_user": "${SCRAPER_POSTGRES_USER}",
  "postgres_password": "${SCRAPER_POSTGRES_PASSWORD}",
  "postgres_sslmode": "${POSTGRES_SSLMODE}",
  "input_schema": "raw",
  "input_table": "id_matching",
  "output_schema": "raw",
  "output_table": "allocine_data",
  "input_id_column": "VISA",
  "input_visa_column": "VISA",
  "input_title_column": "TITRE",
  "input_year_column": null,
  "input_allocine_id_column": "ID_ALLOCINE",
  "input_allocine_url_column": null,
  "scrape_limit": 10,
  "playwright_ws_endpoint": "${PLAYWRIGHT_WS_ENDPOINT:-ws://browserless:3000}"
}
```

Si `database_url` est fourni, il remplace les champs Postgres individuels.

Le fichier `config.json` du dossier est le fichier de configuration runtime utilise par les commandes locales et Docker. Il est versionne dans ce repo.

Les valeurs au format `${ENV_VAR:-default}` du `config.json` sont résolues depuis l'environnement du runtime.

Les accès PostgreSQL sont isolés via `SCRAPER_POSTGRES_USER` et `SCRAPER_POSTGRES_PASSWORD`. `POSTGRES_SSLMODE` pilote le mode TLS pour ce scraper, sans valeur SSL codée en dur. Voir `ingestion/README.md` pour créer le rôle et ses droits.

Dans l'environnement Airbyte actuel, la table source par défaut est `raw.id_matching` et reprend les noms de colonnes bruts du sheet (`VISA`, `TITRE`, `ID_ALLOCINE`). Les champs absents comme l'année CNC ou l'URL Allociné peuvent être laissés à `null`.

La configuration applique actuellement `scrape_limit: 10`, ce qui borne les runs de debug et évite un scraping trop large par défaut. Ajuster cette valeur, la mettre à `null` ou la supprimer pour changer le volume traité.

Fichiers fournis dans le repo:

1. `config.json`: configuration runtime
2. `catalog.template.json`: squelette de catalogue compatible Airbyte, conservé pour compatibilité CLI
3. `build_local_image.sh`: build local de l'image Docker
4. `run_local_spec.sh`: test `spec`
5. `run_local_check.sh`: test `check`
6. `run_local_read.sh`: test `read`
7. `../../docker-compose.yml`: stack locale `prefect-server` + `prefect-worker` + `browserless`
8. `../../prefect/flows.py`: flow Prefect versionné pour l'orchestration

## Initialisation de la table de sortie

Au premier `sync` ou `read`, le job crée automatiquement la table configurée par `output_schema` + `output_table` si elle n'existe pas encore.

Exemple par défaut:

1. schéma: `raw`
2. table: `allocine_data`

Cette table sert de mémoire d'exécution pour la logique de skip incrémental.

Index créés au bootstrap:

1. `source_record_id`
2. `scrape_status`
3. `extracted_at`

## Commands

La commande `read` transmet la configuration au connecteur via son paramètre `raw_config` et émet les résultats en messages JSON `RECORD` sur la sortie standard. La commande `sync`, utilisée par Prefect, écrit les résultats en base.

Depuis la racine du repo:

```bash
python3 ingestion/scraping/allocine/main.py spec
python3 ingestion/scraping/allocine/main.py check --config /tmp/allocine-config.json
python3 ingestion/scraping/allocine/main.py discover --config /tmp/allocine-config.json
python3 ingestion/scraping/allocine/main.py read --config /tmp/allocine-config.json --catalog /tmp/allocine-catalog.json
python3 ingestion/scraping/allocine/main.py sync --config /tmp/allocine-config.json
```

Via Docker:

```bash
bash ingestion/scraping/allocine/build_local_image.sh
bash ingestion/scraping/allocine/run_local_spec.sh
bash ingestion/scraping/allocine/run_local_check.sh reveler/source-allocine:dev ingestion/scraping/allocine/config.json
bash ingestion/scraping/allocine/run_local_read.sh reveler/source-allocine:dev ingestion/scraping/allocine/config.json ingestion/scraping/allocine/catalog.template.json
```

Via `docker compose exec` depuis `ingestion/`:

```bash
docker compose exec prefect-worker python3 /app/ingestion/scraping/allocine/main.py spec
docker compose exec prefect-worker python3 /app/ingestion/scraping/allocine/main.py check --config /app/ingestion/scraping/allocine/config.json
docker compose exec prefect-worker python3 /app/ingestion/scraping/allocine/main.py read --config /app/ingestion/scraping/allocine/config.json --catalog /app/ingestion/scraping/allocine/catalog.template.json
docker compose exec prefect-worker python3 /app/ingestion/scraping/allocine/main.py sync --config /app/ingestion/scraping/allocine/config.json
```

## Positionnement dans l'architecture

Dans la stratégie retenue:

1. Airbyte ne pilote pas ce job;
2. Airbyte reste réservé aux Google Sheets source vers `raw`;
3. Prefect orchestre `dbt phase 1` puis ce job de scraping depuis `prefect-worker`;
4. `read` et `catalog.template.json` sont conservés surtout pour compatibilité technique et tests locaux.

Séparation assumée:

1. la phase `dbt` avant scraping est finalisée côté Prefect;
2. la phase `dbt` après scraping exécute `dbt build --select +tag:phase2` quand elle est activée;
3. le flow Prefect peut aussi déclencher les syncs Airbyte par noms de connexions explicites;
4. ce job couvre uniquement la partie scraping Allocine.

## Limites importantes

1. Le mode opératoire principal est `sync`, pas l'enregistrement dans une UI Airbyte.
2. Le bootstrap crée seulement la table mémoire de sortie. Il ne crée jamais la table d'entrée.
3. Si votre destination Airbyte n'expose que des tables `_airbyte_raw_*`, il faut ajouter une couche de compatibilité avant d'utiliser la logique de skip incrémental.
4. Les seeders historiques consomment encore des CSV aujourd'hui. Ce connecteur couvre seulement la partie scraping.
5. Le repo contient `stg_allocine_films` (résultats réussis), `int_allocine_films` (jointure avec les identifiants de films) et `v_allocine_pipeline_status` (suivi opérationnel). La phase `phase2` sélectionne aussi les modèles intermédiaires et finaux via les tags hérités du projet ; le modèle intermédiaire ne déduplique pas les tentatives par enregistrement source.
6. le port hôte de `browserless/chrome` est piloté par `BROWSERLESS_PORT` dans `.env`;
7. le service `browserless/chrome` du compose local est une commodité de dev; il peut être remplacé par un endpoint Browserless/Chrome distant.
8. Le flow Prefect versionné est le point d'entrée recommandé pour ce scraping en environnement local ou serveur.
9. En cas de blocage anti-bot ou de rate limiting côté site, le scraper enregistre désormais `scrape_status = blocked` avec un message d'erreur explicite.

## Referenced by

- [database/data/allocine/README.md](../../../database/data/allocine/README.md)

## Affiches : migration et reprise explicite

`poster_url` est une URL distante nullable dans `raw.allocine_data`, puis dans
`stg_allocine_films`. L'absence d'affiche produit `NULL` sans faire échouer
la collecte. Aucun fichier image n'est téléchargé durablement. Le téléchargement,
la compression sans perte et le catalogue de fichiers relèvent du futur module
`ml-image` ; aucun MinIO ni CSV n'intervient dans ce parcours.

### Mise en service

Les migrations ingestion sont des scripts SQL versionnés sous `infra/data/`,
indépendants des migrations Alembic applicatives. Sur une table existante,
appliquer le script suivant **avant** le nouveau connecteur et la phase dbt 2,
avec le propriétaire de la table ou un administrateur. Vérifier la base cible
avec `SELECT current_database(), current_user;`.

Depuis la racine du dépôt, avec un service libpq administrateur configuré :

```bash
psql "service=ric-admin" -X -v ON_ERROR_STOP=1 -c 'SELECT current_database(), current_user;'
psql "service=ric-admin" -X -v ON_ERROR_STOP=1 -f infra/data/2026-10-15-allocine-poster-url.sql
```

Le script est transactionnel et rejouable : `ADD COLUMN IF NOT EXISTS poster_url TEXT`
préserve les lignes et les URL existantes. Il crée aussi le journal
`raw.allocine_data_poster_backfill`. Il exige que `raw.allocine_data` existe.
Sur une installation neuve, le connecteur crée cette table avec `poster_url` ;
appliquer ensuite le script pour disposer du journal avant tout backfill.

Le connecteur ne migre pas automatiquement les tables existantes.
Pour une sortie personnalisée, adapter les références `raw.allocine_data` et
`raw.allocine_data_poster_backfill` dans une copie du SQL ; le backfill utilise
`output_schema` et `output_table + "_poster_backfill"`.

Si le journal appartient à un rôle différent du scraper, accorder les droits :

```sql
GRANT USAGE ON SCHEMA raw TO scraper_user;
GRANT SELECT, UPDATE ON raw.allocine_data TO scraper_user;
GRANT SELECT, INSERT ON raw.allocine_data_poster_backfill TO scraper_user;
GRANT USAGE, SELECT ON SEQUENCE raw.allocine_data_poster_backfill_attempt_id_seq TO scraper_user;
```

### Backfill

Le scraping normal continue d'ignorer les collectes terminées. La commande
`backfill-posters` sélectionne séparément les couples
`(source_record_id, allocine_id)` ayant au moins une collecte `success`
avec `poster_url IS NULL`, un identifiant source non nul et un identifiant
Allociné positif. Elle recharge uniquement la fiche film, sans recherche ni casting.

Depuis la racine, après migration :

```bash
# Lecture seule : ni écriture, ni navigateur, ni requête Allociné.
python3 -m ingestion.scraping.allocine.main backfill-posters --config ingestion/scraping/allocine/config.json --dry-run --limit 20

# Sélection ciblée par source_record_id, option répétable.
python3 -m ingestion.scraping.allocine.main backfill-posters --config ingestion/scraping/allocine/config.json --dry-run --source-id 123 --source-id 456

# Exécution volontaire, après contrôle de la sélection.
python3 -m ingestion.scraping.allocine.main backfill-posters --config ingestion/scraping/allocine/config.json --limit 20

# Rafraîchir le staging matérialisé, depuis ingestion/dbt et avec le profil configuré.
dbt build --select stg_allocine_films
```

`--limit` borne les couples source/Allociné, pas les lignes historiques modifiées.
Sans limite, tous les couples éligibles sont sélectionnés ; `scrape_limit` du
scraping normal ne s'applique pas. `--source-id` désigne un identifiant exact
de `source_record_id`, pas un `allocine_id`. La limite s'applique après filtrage.
Les collectes sans identifiant Allociné exploitable sont exclues et nécessitent
une correction du matching, hors de ce backfill.

Chaque film a sa transaction. Seul `poster_url` est modifié, uniquement sur les
lignes réussies encore à `NULL` au moment de l'écriture. Une URL déjà présente
reste intacte, y compris si elle arrive après la sélection. Les doublons historiques
du même couple sont enrichis ensemble. Les autres champs, notamment `run_id`,
`extracted_at`, `scrape_status`, `error_message` et `record_hash`, sont conservés.
Le hash reste celui de la collecte initiale, pas celui de la ligne enrichie.

Le journal conserve le run de backfill, la date de tentative, les identifiants,
l'URL de fiche, l'URL d'affiche obtenue, le statut, l'erreur éventuelle et le nombre
de lignes modifiées. Statuts : `updated`, `missing`, `error`, `unchanged`.
La mise à jour et son journal sont atomiques. En cas d'erreur SQL, cette transaction
est annulée ; l'erreur est signalée dans la sortie du CLI, puis le film suivant
est traité. Conserver les logs du CLI, notamment si le journal est indisponible.
Le CLI termine avec le code 1 si au moins un film échoue, 0 sinon.

Une affiche absente laisse la collecte réussie et son URL à `NULL`. Les absences
et erreurs restent éligibles au prochain lancement. Les couples jamais tentés
passent avant ceux déjà journalisés, puis les plus anciennes tentatives passent
en premier : une petite limite ne bloque pas indéfiniment les films suivants.
Les couples enrichis ne sont plus sélectionnés. Une interruption laisse les
transactions déjà validées disponibles pour la reprise.

Le backfill est séquentiel, respecte les délais inter-films et le timeout
`record_timeout_seconds`. Une session navigateur est ouverte par film.
Éviter les lancements simultanés pour limiter les requêtes redondantes :
les écritures sont protégées, mais aucune réservation distribuée n'est effectuée.
Une URL stockée ne garantit ni disponibilité future ni présence d'un fichier local.
Les modèles aval actuels utilisent des projections explicites ; aucune extension
de `int_allocine_films` ou des tables finales n'est nécessaire pour ce champ.

### Tests sans Allociné

Installer les dépendances du scraper, `pytest` et `PyYAML`, puis lancer depuis la racine :

```bash
python3 -m pytest -q tests/ingestion
RIC_POSTER_TEST_DB=1 python3 -m pytest -q tests/ingestion
```

La première commande ignore les tests PostgreSQL. La seconde utilise les paramètres
de `ingestion/.env` via `config.json`, avec le compte scraper. Elle exige le droit
`TEMP` sur la base. Toutes les tables de test vivent dans le schéma temporaire
de session et disparaissent à la déconnexion ; aucune table métier n'est lue
ou modifiée. Le SQL de migration est rejoué en remplaçant uniquement son schéma
par ce schéma temporaire. Les fixtures HTML et un navigateur simulé empêchent
les appels réels à Allociné. Le SQL du staging est aussi exécuté sur ces fixtures ;
cela ne remplace pas un `dbt build` de mise en service.

## Backfill local et transfert vers production

Le navigateur peut tourner sur le poste local et écrire dans la base staging
configurée par `ingestion/.env`. Les identifiants staging/production doivent être
alignés. Appliquer la migration et les droits décrits ci-dessus sur staging avant
le lancement. Installer Chromium avec la version Playwright du runtime :

```bash
python3 -m playwright install chromium
python3 -m ingestion.scraping.allocine.poster_campaign \
  --config ingestion/scraping/allocine/config.json \
  --output-dir ingestion/scraping/allocine/local-runs/campagne-001 \
  --batch-size 10
```

La campagne force Chromium local, même si le JSON indique Browserless. Elle fige
la sélection initiale, traite chaque couple une seule fois et produit un export
SQL après chaque lot. Aucun CSV ni fichier image n'est créé. Le poste doit rester
allumé, connecté et éveillé pendant l'exécution. Le répertoire `local-runs/` est
ignoré par Git. Chaque lancement exige un nouveau sous-répertoire.

Fichiers produits :

- `posters.sql` : dernier export complet disponible, remplacé atomiquement.
- `progress.json` : compteurs du traitement et statut final.
- `candidates.json` : sélection initiale pour retrouver le périmètre.
- `campaign.pid` : PID historique du processus ; sa présence ne prouve pas qu'il tourne.

Créer un fichier `STOP` dans le dossier de campagne, ou envoyer SIGINT/SIGTERM,
arrête le traitement après le lot courant et sauvegarde l'export. Un lot composé
uniquement d'erreurs arrête aussi la campagne. Les affiches absentes ne sont pas
retentées en boucle. Pour reprendre après interruption, relancer dans un nouveau
dossier : les URL déjà renseignées seront ignorées. Une panne brutale conserve
le dernier export terminé ; les succès plus récents restent dans staging et
peuvent être réexportés sans scraping.

Export seul, depuis staging, vers un fichier nouveau :

```bash
python3 -m ingestion.scraping.allocine.poster_export \
  --config ingestion/scraping/allocine/config.json \
  --output ingestion/scraping/allocine/local-runs/affiches-production.sql
```

L'option `--run-id` restreint l'export à un run de backfill. Sans cette option,
l'export inclut tous les couples enrichis et journalisés avec le statut `updated`,
dont l'URL correspond encore à une collecte réussie dans staging. Les données
exportées se limitent aux deux identifiants, à l'URL d'affiche et aux métadonnées
de provenance : run, date de récupération et URL de fiche. En cas de plusieurs
tentatives, la dernière correspondance est retenue. Les anciennes URL sans
journal de backfill ne sont pas exportées.

Sur production, appliquer d'abord la migration additive, puis charger le SQL
avec un service libpq pointant explicitement vers production :

```bash
psql 'service=ric-production-admin' -X -v ON_ERROR_STOP=1 \
  -c 'SELECT current_database(), current_user;'
psql 'service=ric-production-admin' -X -v ON_ERROR_STOP=1 \
  -f infra/data/2026-10-15-allocine-poster-url.sql
psql 'service=ric-production-admin' -X -v ON_ERROR_STOP=1 \
  -f ingestion/scraping/allocine/local-runs/affiches-production.sql
```

L'import utilise une table temporaire et une transaction. Il enrichit uniquement
les collectes `success` avec URL à `NULL`, jointes sur `source_record_id` et
`allocine_id`. Il conserve les autres colonnes et les URL déjà présentes. Seules
les lignes réellement modifiées génèrent une entrée du journal ; rejouer le même
fichier n'ajoute pas de doublon d'audit. Le journal conserve le run et la date de
récupération staging. L'import échoue atomiquement si une écriture est impossible.
Il cible toujours `raw.allocine_data`, même si l'export utilise une autre source.
Les identifiants sans correspondance en production ne modifient aucune ligne.
Rafraîchir ensuite `stg_allocine_films` avec le profil dbt production approprié.
