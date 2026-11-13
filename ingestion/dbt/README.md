# dbt ingestion

## Metadata du document

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-13

**Status:** actif

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-26 | Joel Teixeira | Documentation du projet dbt ingestion, des tags phase1/phase2 et du schéma `ops` |
| 2 | 2026-10-06 | Joel Teixeira | Suppression des déclarations de modèles absents et alignement des modèles documentés sur le code actuel |
| 3 | 2026-10-10 | Joel Teixeira | Ajout du runbook local macOS/WSL2 pour le debug et dbt Docs |
| 4 | 2026-10-11 | Joel Teixeira | Normalisation des espaces dans les budgets CNC avant conversion numérique. Inclusion des modèles intermédiaires et finaux dans la phase 2, avec leurs dépendances amont. Alignement des clés des corrections, identifiants des sociétés et avertissements sur les correspondances externes absentes ou dupliquées. Historisation des résultats et détails dbt pour Metabase, quarantaine des crédits sans film et harmonisation des types dans les jointures Mubi |
| 5 | 2026-10-15 | Joel Teixeira | URL d’affiche nullable dans le staging Allociné ; prérequis de migration. |
| 6 | 2026-11-11 | Joel Teixeira | Couverture des 29 genres observés : corrections orthographiques, classement du Péplum et catégories explicites Divers, Erotique et Évènement Sportif. |
| 7 | 2026-11-12 | Joel Teixeira | Alignement des corrections sur le schéma Airbyte : clés composées des crédits et genres, retrait du champ Allociné des rôles et filtre GENRE_ID. Dashboard Metabase de revue du scraping Allociné, des écarts de visa et des recherches sans résultat (`not_found`). |
| 8 | 2026-11-13 | Joel Teixeira | Intégration des ajouts manuels de personnes et crédits, dernier succès Allociné par visa, contrôles de références et conversion du crédit d’impôt. |
| 9 | 2026-11-13 | Joel Teixeira | Prise en charge de la date et de l’heure dans UPDATED_DATE pour toutes les sources GSheet concernées, rétrocompatibilité et tri des corrections. |

Projet dbt Core exécuté depuis `prefect-worker`.

## Rôle

1. Lire les sources `raw` chargées par Airbyte ou par le scraper Allociné.
2. Normaliser les données dans `staging`.
3. Consolider les vues intermédiaires dans `intermediate`.
4. Publier les tables finales dans `fnl` quand elles existent.
5. Publier les vues opérationnelles dans `ops`.

`stg_allocine_films.poster_url` expose l’URL distante nullable de l’affiche. Appliquer la [migration ingestion](../../infra/data/2026-10-15-allocine-poster-url.sql) avant de reconstruire ce modèle sur une base existante. Le [guide Allociné](../scraping/allocine/README.md#affiches--migration-et-reprise-explicite) décrit le backfill explicite et les droits requis. Aucun fichier image n’est stocké par dbt. Les projections aval restent inchangées.

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

1. `phase1`: `stg_cnc_films`, préparation CNC après Airbyte.
2. `phase2`: `stg_allocine_films`, `v_allocine_pipeline_status` et tous les modèles des dossiers `intermediate/` et `fnl/`, exécutés après la phase 1 avec les résultats de scraping déjà disponibles. Les deux dossiers héritent du tag dans `dbt_project.yml`.

Le flow Prefect principal exécute toujours `tag:phase1`. Il exécute `+tag:phase2` seulement quand le paramètre `run_dbt_phase_2_step` est activé.

Le préfixe `+` inclut les dépendances amont, notamment les modèles de staging non taggés. La finalisation construit ainsi les modèles `intermediate` et `fnl` et exécute les tests associés. La phase 1 reste limitée à `stg_cnc_films`.

Toutes les sources brutes référencées doivent exister et être lisibles par `dbt_user`, y compris les tables de corrections et les sorties Mubi. Le flow principal ne lance aucun scraper ; les sources Allociné et Mubi sont alimentées par leurs déploiements manuels séparés. Un échec de construction ou de test fait échouer la finalisation.

Pour vérifier le périmètre sans écrire en base, remplacer `dbt build` par `dbt ls --resource-type model` dans la commande de phase 2. Après déploiement du worker mis à jour, cette commande de build permet aussi de reconstruire les couches manquantes sans relancer Airbyte ni le scraping.

## Modèles opérationnels

1. `staging.stg_cnc_films`: projection typée de `raw.films`.
2. `staging.stg_allocine_films`: projection typée des résultats réussis de `raw.allocine_data`.
3. `intermediate.int_cnc_films`: transformations métier CNC et jointure avec `stg_id_matching`.
4. `intermediate.int_allocine_films`: projection des données Allociné et jointure avec `stg_id_matching`.
5. `ops.v_allocine_pipeline_status`: vue dashboard Metabase pour le suivi Allociné.

Le staging Allociné conserve le dernier succès par visa source (repli sur `source_record_id` si le visa est absent), selon `extracted_at`, puis `run_id` et `record_hash`. Une tentative ultérieure en erreur ne remplace pas ce succès. Les visas absents ou encore dupliqués font échouer le test dédié. Le rapprochement des métadonnées Allociné utilise le visa et l’identifiant Allociné ; la table finale joint ces métadonnées par `film_id`. Des visas distincts partageant un identifiant Allociné restent signalés dans les contrôles de matching. Cette règle ne valide pas l’identité d’un ancien résultat de scraping.

## Classification des genres

Le `CASE` de `int_film_genres` classe `Judiciaire` dans `Aventure/Policier/Thriller` et accepte `Epouvante-horreur` avec ou sans accent initial pour `Fantastique/Horreur/SF`. `Péplum` rejoint `Biopic/Guerre/Histoire`. `Divers`, `Erotique` et `Évènement Sportif` conservent chacun une catégorie explicite. Ce mapping couvre les 29 genres distincts observés dans `staging.stg_allocine_films` le 11 novembre 2026. Les nouveaux genres sans correspondance restent nuls et font échouer les tests de présence des tables finales : ajouter leur classement explicitement, sans catégorie de repli « Autre ».

## Qualité des identifiants

Les corrections de nominations utilisent `award_nomination_id`. Les corrections de crédits sont dédupliquées par `(film_id, role_id, credit_holder_id)` et celles des associations film-genre par `(film_id, genre_id)`, en conservant la date de correction la plus récente. Les tests contrôlent la présence des composants et l’unicité de chaque association ; les anciens champs `film_credit_id` et `film_genre_id` ne sont plus exposés. Le référentiel des genres utilise `GENRE_ID` et `GENRE_NAME` dans la source ; le filtre de la ligne exemple porte sur `GENRE_ID`. Les corrections de rôles n’exposent plus `allocine_name`, absent de la source.

Dans Airbyte, ne pas dédupliquer `film_credits` sur `CREDIT HOLDER ID` seul : une personne peut avoir plusieurs rôles et films. Utiliser une clé composée des trois champs ou le mode overwrite sans déduplication. dbt ne peut pas restaurer les associations supprimées en amont.

Dans `int_id_matching`, `film_id` et `cnc_visa` doivent être renseignés et uniques. Le titre `cnc_name` doit être renseigné mais peut être partagé par plusieurs films. Les tests de présence et d'unicité des identifiants Allociné, Mubi et TMDB ont une sévérité `warn`. Les tests d'unicité de `fnl_films.film_id` et `fnl_films.cnc_visa` sont bloquants : la table finale doit contenir une ligne par film. Les avertissements sur les identifiants externes ne sont pas transformés en erreurs via `--warn-error`.

Dans `int_credit_holders_role`, les identifiants des personnes restent dérivés de leur nom complet. Ceux des sociétés sont dérivés de `company:` suivi de leur raison sociale, car leur champ `full_name` est nul. Une raison sociale absente ou vide ne produit pas d'identifiant valide : le test final `not_null` reste bloquant. Cette convention n'effectue pas de résolution des homonymes.

Les crédits dont `film_id` est nul sont exclus de `fnl_film_credits` et conservés dans `ops.film_credits_unmatched`. Cette quarantaine expose l'identifiant Allociné, la personne ou société, le rôle et les visas/titres des entrées de scraping à examiner. Le test `film_credits_unmatched_review` signale leur présence avec une sévérité `warn`. Aucune correspondance n'est attribuée automatiquement par titre ou par visa de la requête de scraping. Les personnes et sociétés restent dans leur référentiel final.

Les jointures intermédiaires Mubi convertissent les identifiants numériques du scraping en texte pour les comparer aux identifiants du matching.

## Suivre la qualité dbt dans Metabase

Le hook `on-run-end` du projet appelle [persist_dbt_results](macros/persist_dbt_results.sql) après `build`, `test`, `run`, `seed` et `snapshot`. Il historise les résultats des modèles et tests, y compris les avertissements, erreurs et éléments ignorés :

- `ops.dbt_run_results` : une ligne par invocation et ressource dbt ; statut, modèle, colonne, nombre d'anomalies, durée et message.
- `ops.dbt_test_failures` : les lignes concernées, en JSON, pour les tests en avertissement ou en échec configurés avec `store_failures: true`.
- `ops.v_dbt_latest_results` : dernier résultat observé par ressource. Un run partiel ne masque pas les derniers résultats des autres contrôles.

Les contrôles non bloquants et le contrôle de quarantaine utilisent le stockage natif des échecs dbt dans `ops`. Le hook recopie leurs détails avec l'identifiant d'invocation, afin de conserver l'historique même lorsque dbt reconstruit les tables techniques du test. Les tables `id_matching_duplicates` et `allocine_duplicates` ne sont pas nécessaires. Les résultats centraux sont lisibles par `metabase_ops_user` ; les sources restent inchangées.

Pour un test `unique`, le nombre d'anomalies compte les **valeurs dupliquées**, et le détail contient `unique_field` et `n_records`. Pour `not_null`, il compte les **lignes** et le détail conserve les colonnes de la ligne. Ne pas additionner ces nombres comme un total de films : plusieurs tests peuvent signaler les mêmes données. Les détails sont joints à la même invocation que le résultat affiché. La requête de rapprochement des doublons utilise ensuite la version actuelle de `raw.id_matching` pour retrouver les titres et visas source.

La collecte commence au déploiement du hook ; les anciens logs ne sont pas importés. Une interruption brutale ou une erreur de compilation avant le hook peut empêcher l'enregistrement du run : conserver les logs Prefect pour ces cas. Les résultats sont conservés sans purge automatique.

Le dashboard « Qualité des données — dbt » comprend trois indicateurs (tests en avertissement, erreurs bloquantes, crédits isolés), les contrôles à examiner, les correspondances source à revoir, les détails et l'historique. Les requêtes sont versionnées dans [analyses/metabase](analyses/metabase). Prévisualisation sans clé ni appel réseau, depuis la racine :

```bash
python3 infra/data/metabase-dbt-quality.py --preview
```

Création ou mise à jour via l'API Metabase, avec une clé disposant des droits sur la connexion `cinestats-ops-db` et la collection choisie :

```bash
python3 infra/data/metabase-dbt-quality.py \
  --url https://<metabase> \
  --api-key-file /chemin/protege/cle-api-metabase \
  --collection-id <id-collection> \
  --state-file /chemin/persistant/dashboard-dbt-state.json
```

La clé reste hors Git et hors ligne de commande. Le fichier d'état conserve les identifiants du dashboard et des questions pour les actualisations ; le réutiliser évite les créations multiples. Le script conserve les cartes ajoutées manuellement. Aucune publication publique ni modification des permissions Metabase n'est effectuée. L'accès API doit être fourni séparément ; la connexion SSH au serveur ne remplace pas une authentification Metabase.

Après déploiement, relancer `dbt build --select +tag:phase2` avec les options de profil ci-dessus. Cela reconstruit les finales et la quarantaine, teste les données puis alimente le suivi. `dbt parse` vérifie la configuration mais ni les données ni l'exécution SQL.

## Examiner les correspondances du scraping dans Metabase

Le dashboard [Scraping Allociné — À examiner](https://metabase.cinestats5050.fr/dashboard/7) lit directement `raw.allocine_data`
sur la connexion `cinestats-ops-db`. Il comporte quatre compteurs (total, `needs_review`,
`visa_mismatch`, `not_found`) et trois tables détaillées, avec filtres **Visa CNC** (égalité exacte)
et **Titre contient** (recherche sans distinction de casse, CNC ou Allociné).
Les tables affichent les titres, visas attendu et trouvé, réalisateur Allociné,
motif, liens de vérification et dernière tentative en heure de Paris, par ancienneté.

La [requête commune](analyses/metabase/scraping_review_queue.sql) classe **tous**
les statuts avant de sélectionner les anomalies. Une seule tentative est retenue
par `source_record_id`, avec repli sur le visa puis l'empreinte pour les lignes sans
identifiant. Les dates nulles passent après les dates connues ; les égalités sont
départagées par run et empreinte. Sans séquence d'insertion, deux tentatives au même
instant ne permettent pas de prouver leur ordre chronologique.
Une réussite plus récente retire donc le film de cette file ; un ancien écart ne
reste pas affiché après résolution. Le compteur mesure les identifiants source,
pas les tentatives. Aucun historique de validation humaine n'est créé.

`needs_review` signifie une correspondance non confirmée ; `visa_mismatch` indique
un visa Allociné différent du visa source. Le diagnostic peut détailler plusieurs
candidats, sans candidat retenu ni visa Allociné unique. Les anciens résultats ne
sont pas requalifiés automatiquement. `not_found` signale une recherche sans résultat :
vérifier manuellement le titre et l'identifiant Allociné. Ce statut est considéré
comme terminé par le scraper et ne déclenche pas de reprise automatique.
Les erreurs techniques (`error`, `blocked`) restent hors périmètre.
La vue `ops.v_allocine_pipeline_status`, issue du staging filtré
sur `success`, ne peut pas alimenter cette file. Aucun run dbt n'est nécessaire.

Depuis la racine, vérifier puis créer ou actualiser le dashboard :

```bash
python3 infra/data/metabase-scraping-review.py --preview
python3 infra/data/metabase-scraping-review.py \
  --url https://metabase.cinestats5050.fr \
  --env-file ingestion/.env --collection-id 7 --check
python3 infra/data/metabase-scraping-review.py \
  --url https://metabase.cinestats5050.fr \
  --env-file ingestion/.env --collection-id 7
```

`METABASE_API_KEY` peut venir de l'environnement, du fichier `.env` explicite
(`python-dotenv` requis), ou de `--api-key-file`. La clé n'est jamais imprimée.
`--check` exécute les sept requêtes sans créer de question ni dashboard.
Le compte Metabase doit pouvoir lire `raw.allocine_data` et écrire dans la
collection Operations (ID 7 sur cette instance). Aucun droit ni accès public
n'est modifié ; les permissions existantes de la collection s'appliquent.

Conserver le fichier d'état local ignoré par Git
`ingestion/scraping/allocine/local-runs/metabase-review-state.json` : il contient
uniquement l'URL, les identifiants Metabase et la collection. Le réutiliser permet
les mises à jour sans doublons ; `--state-file` permet un autre emplacement.
Les cartes et filtres ajoutés manuellement sont conservés. Actualiser le dashboard
dans Metabase pour relire les résultats ; aucune relance de scraper ni correction
source n'est déclenchée par sa consultation.

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

## Ajouts manuels de réalisateurs et autres crédits

`fnl_credit_holders` inclut les personnes présentes uniquement dans `credit_holders`.
Les champs manuels non vides priment sur les valeurs issues du scraping ; un champ
vide ne supprime pas une valeur existante. Les identifiants doivent être des UUID
cohérents avec les personnes existantes. Une correction ne rapproche pas des
homonymes et ne fusionne pas deux UUID automatiquement.

`fnl_film_credits` réunit les crédits scrapés et `int_fix_film_credits` avec une
association unique par `(film_id, role_id, credit_holder_id)`. Une ligne manuelle
est un ajout, pas une demande de remplacement ou de suppression. Le film et le
rôle doivent déjà exister ; une nouvelle personne peut être ajoutée dans
`credit_holders` pendant la même synchronisation Airbyte. Les tests vérifient les
trois références ainsi que la conservation de chaque correction.

Les deux stagings concernés acceptent tous les auteurs, y compris Hugo Laurens.
Ils excluent explicitement les lignes de démonstration observées : la personne
`000a676c-8ef7-5b14-8a67-9431ceeb933e` nommée `Example Example`, et l’association
film `0016b072-7ad8-f224-cfd7-053b56ff2720`, rôle
`d894803c-210d-2b5b-6e7e-50f2d418bfcf`, personne
`d8f8d53c-51b8-f89b-1a8d-da48da142694`, datée du 25/04/2026 par Hugo Laurens.
Les filtres des autres onglets de correction ne sont pas modifiés.
Les dates et auteurs doivent être renseignés. Les valeurs vides des champs de
personne sont normalisées en NULL avant l’application des corrections.

`CREDIT_D_IMPOT` reconnaît `X` et `OUI`, sans distinction de casse et après
suppression des espaces extérieurs. Le code `D`, dont le sens reste à confirmer,
est conservé comme valeur inconnue (`NULL`), et non assimilé à une absence d’aide.

### Vérifications

Les tests singuliers contrôlent l’unicité des crédits, les visas Allociné et la
conservation des ajouts manuels. Les tests de schéma contrôlent les références et
l’unicité des personnes et films. Les tests SQL de régression utilisent des CTE
fictives en transaction `READ ONLY`, sans création de schéma ni écriture :

```bash
DBT_TEST_SSH=<alias-ssh> DBT_TEST_DATABASE=<base-postgresql> \
  ingestion/dbt/.venv-dbt/bin/python -m unittest discover \
  -s tests/ingestion -p test_dbt_manual_recovery.py -v
```

Le compte SSH doit permettre `sudo -n -u postgres psql`. La base doit disposer de
l’extension `unaccent`, utilisée par le modèle CNC. Sans `DBT_TEST_SSH`, ces tests
sont ignorés explicitement. Ils couvrent les ajouts, les overrides, les doublons,
les lignes exemples, les corrections de Hugo, les reprises après erreur et les
codes de crédit d’impôt. Ils ne remplacent pas un `dbt build` complet avant livraison.

## Date et heure des mises à jour GSheet

Les 12 stagings qui lisent `UPDATED_DATE` utilisent la macro commune
`gsheet_updated_timestamp`. Le nom de colonne dbt `updated_date` reste inchangé,
mais son type devient `timestamp without time zone` au lieu de `date`.
Cela couvre `films`, `id_matching` et les dix sources de corrections.
Aucune colonne `TIME` supplémentaire n’est nécessaire.

Format recommandé dans la cellule : **`13/11/2026 15:42:08`**, soit
`DD/MM/YYYY HH:MM:SS` avec une heure sur 24 heures. Les valeurs avec heures et
minutes seules sont acceptées. Les anciennes dates seules restent valides et
valent minuit. Les dates ISO `YYYY-MM-DD`, avec la même heure facultative, sont
également acceptées. Les espaces extérieurs sont supprimés ; une cellule vide
est convertie en NULL. Une date impossible ou un format non pris en charge fait
échouer la conversion, sans ignorer silencieusement l’heure.

Conserver le même fuseau de référence, Europe/Paris, dans tous les GSheets :
la valeur est une heure locale, sans conversion de fuseau dans dbt. Airbyte doit
continuer à transmettre une chaîne, pas un numéro de série de date Google Sheets.
Les dates de naissance et de nomination restent des dates, sans heure.

Les dix modèles `int_fix_*` classent les corrections par date et heure
complètes, puis par date d’extraction Airbyte et identifiant de ligne Airbyte
pour départager les égalités. Les valeurs NULL sont classées en dernier.
L’ordre physique des lignes n’est pas utilisé. Deux corrections contradictoires
avec le même horodatage restent à éviter : les métadonnées techniques ne
traduisent pas l’intention métier et peuvent changer après une nouvelle sync.
Les modèles de films et de matching ne gagnent pas de déduplication supplémentaire.

Déployer le code avant de modifier le format des GSheets, puis reconstruire les
stagings et leurs dépendances via le pipeline complet. Le parsing dbt et les
tests SQL vérifient les anciennes dates, les heures/minutes/secondes, les dates
invalides et la priorité des corrections indépendamment de leur ordre d’entrée.
