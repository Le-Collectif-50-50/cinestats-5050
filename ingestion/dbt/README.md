# dbt ingestion

## Metadata du document

**Owner:** Data Team DataForGood

**Dernière révision:** 2026-10-11

**Status:** actif

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-26 | Joel Teixeira | Documentation du projet dbt ingestion, des tags phase1/phase2 et du schéma `ops` |
| 2 | 2026-10-06 | Joel Teixeira | Suppression des déclarations de modèles absents et alignement des modèles documentés sur le code actuel |
| 3 | 2026-10-10 | Joel Teixeira | Ajout du runbook local macOS/WSL2 pour le debug et dbt Docs |
| 4 | 2026-10-11 | Joel Teixeira | Normalisation des espaces dans les budgets CNC avant conversion numérique. Inclusion des modèles intermédiaires et finaux dans la phase 2, avec leurs dépendances amont |

Projet dbt Core exécuté depuis `prefect-worker`.

## Rôle

1. Lire les sources `raw` chargées par Airbyte ou par le scraper Allociné.
2. Normaliser les données dans `staging`.
3. Consolider les vues intermédiaires dans `intermediate`.
4. Publier les tables finales dans `fnl` quand elles existent.
5. Publier les vues opérationnelles dans `ops`.

Le staging `stg_cnc_films` retire les espaces classiques, insécables (U+00A0) et fines insécables (U+202F) de `DEVIS`, puis remplace la virgule décimale par un point avant conversion numérique. La multiplication par un million pour les années d'agrément à partir de 2013 reste inchangée.

## Exécution

Pour travailler sans conteneur sur macOS ou Windows via WSL2, suivre le [runbook dbt local](runbook_dbt_local.md) : environnement `.venv-dbt`, connexion, tests et serveur dbt Docs.

Depuis le container worker:

```bash
dbt parse --profile ric --project-dir /app/ingestion/dbt
dbt build --profile ric --project-dir /app/ingestion/dbt --select tag:phase1
dbt build --profile ric --project-dir /app/ingestion/dbt --select +tag:phase2
```

Depuis la racine du repo:

```bash
docker compose -f ingestion/docker-compose.yml exec prefect-worker dbt parse --profile ric --project-dir /app/ingestion/dbt
docker compose -f ingestion/docker-compose.yml exec prefect-worker dbt build --profile ric --project-dir /app/ingestion/dbt --select tag:phase1
docker compose -f ingestion/docker-compose.yml exec prefect-worker dbt build --profile ric --project-dir /app/ingestion/dbt --select +tag:phase2
```

## Tags

1. `phase1`: `stg_cnc_films`, exécuté avant scraping Allociné.
2. `phase2`: `stg_allocine_films`, `v_allocine_pipeline_status` et tous les modèles des dossiers `intermediate/` et `fnl/`, exécutés après scraping Allociné. Les deux dossiers héritent du tag dans `dbt_project.yml`.

Le flow Prefect principal exécute toujours `tag:phase1`. Il exécute `+tag:phase2` seulement quand le paramètre `run_dbt_phase_2_step` est activé.

Le préfixe `+` inclut les dépendances amont, notamment les modèles de staging non taggés. La finalisation construit ainsi les modèles `intermediate` et `fnl` et exécute les tests associés. La phase 1 reste limitée à `stg_cnc_films`.

Toutes les sources brutes référencées doivent exister et être lisibles par `dbt_user`, y compris les tables de corrections et les sorties Mubi. Le flow principal ne lance que le scraping Allociné ; les sources Mubi doivent être alimentées séparément. Un échec de construction ou de test fait échouer la finalisation.

Pour vérifier le périmètre sans écrire en base, remplacer `dbt build` par `dbt ls --resource-type model` dans la commande de phase 2. Après déploiement du worker mis à jour, cette commande de build permet aussi de reconstruire les couches manquantes sans relancer Airbyte ni le scraping.

## Modèles opérationnels

1. `staging.stg_cnc_films`: projection typée de `raw.films`.
2. `staging.stg_allocine_films`: projection typée des résultats réussis de `raw.allocine_data`.
3. `intermediate.int_cnc_films`: transformations métier CNC et jointure avec `stg_id_matching`.
4. `intermediate.int_allocine_films`: projection des données Allociné et jointure avec `stg_id_matching`.
5. `ops.v_allocine_pipeline_status`: vue dashboard Metabase pour le suivi Allociné.

Les modèles intermédiaires CNC et Allociné actuels ne sélectionnent pas automatiquement la dernière version par visa ou par enregistrement source. Les anciennes déclarations YAML de déduplication, dont les fichiers SQL sont absents, ne constituent pas des tests actifs. Leur suppression ne supprime aucune relation PostgreSQL existante.

## Permissions

Le runtime dbt utilise `dbt_user`.

Grants attendus sur la base projet:

```sql
GRANT USAGE, CREATE ON SCHEMA staging TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA intermediate TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA fnl TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA ops TO dbt_user;
GRANT USAGE ON SCHEMA raw TO dbt_user;
```

## Referenced by

- [ingestion/README.md](../README.md)
