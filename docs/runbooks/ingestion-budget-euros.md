# Bascule des budgets CNC en euros exacts — issue #43

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-15

**Status:** active — procédure de migration ; publication à vérifier

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-15 | Joel Teixeira | Contrat des budgets, bascule coordonnée GSheets/Airbyte/dbt, contrôles et retour arrière. |

## Contrat et périmètre

La colonne `DEVIS` de l’onglet `films` du [GSheet CNC](https://docs.google.com/spreadsheets/d/1mvKPVrZ3FAHuUB__3akr4Fr7K4MqgTba9bFwNdtL_To/edit#gid=2065887040) contient des montants numériques en euros. Le connecteur Airbyte actuel transmet leur affichage. Un affichage en millions avec deux décimales perd donc jusqu’à 5 000 € par film.

Le nouveau contrat impose des euros exacts pour toutes les années d’agrément. Appliquer à la seule colonne `DEVIS` un format numérique sans séparateur d’échelle, avec toutes les décimales nécessaires aux valeurs source ; `0.###############` convient aux valeurs numériques Sheets. Ne modifier ni les valeurs, ni les formules, ni les autres colonnes. Vérifier le séparateur décimal affiché selon la locale du classeur.

`stg_cnc_films` retire les espaces U+0020, U+00A0 et U+202F, remplace la virgule décimale par un point et convertit en PostgreSQL `NUMERIC`. Aucun changement d’échelle ne dépend de l’année. Une valeur vide devient `NULL` ; une valeur non numérique provoque une erreur. Il n’existe aucune détection fiable de l’unité par la seule grandeur du montant : le contrat source doit être contrôlé avant chaque changement de format.

Les identifiants, crédits, budgets corrigés éventuels et dashboards conservent leurs règles. Aucun scraping Allociné n’est nécessaire. Les vues et tables en aval doivent être reconstruites pour propager le nouveau type numérique et les valeurs.

## Préparation et exclusion des traitements concurrents

1. Vérifier le commit livré et l’état courant des données. Le diagnostic du 13 novembre porte sur 4 914 films rapprochés par visa, dont la date legacy **ou** dbt est comprise entre 2004 et 2024 inclus : 2 667 budgets différaient de plus de 1 €. Ces nombres sont une référence datée, à actualiser ; distinguer changement de source, de population et correction de précision.
2. Avant modification, lire les valeurs numériques, valeurs affichées et formats de `DEVIS` sur toute la population concernée. Confirmer que les valeurs sous-jacentes sont déjà en euros pour toutes les années. Conserver en mémoire les anciennes valeurs, formules et formats pour la comparaison et le retour arrière ; utiliser l’historique du classeur si la session est interrompue.
3. Attendre la fin des runs Prefect et jobs Airbyte actifs. Suspendre les déclenchements d’ingestion, le poller et toute planification directe Airbyte pendant toute la bascule. Empêcher un lancement manuel concurrent. Ne pas interrompre un run actif pour effectuer cette opération.
4. Relever les effectifs, visas distincts, budgets nuls, doublons de film/crédit et statistiques finales à population et filtres constants. Conserver les résultats en mémoire, sans export de données de diagnostic.

## Ordre de bascule

1. Préparer le code dbt testé sur le worker selon le [runbook stack data](stack-data.md), en maintenant les déclenchements suspendus. Ne lancer aucun ancien dbt sur les nouvelles données, ni le nouveau dbt sur l’ancien affichage en millions.
2. Modifier uniquement `userEnteredFormat.numberFormat` pour la colonne `DEVIS` (hors en-tête), après confirmation de son index dans les métadonnées du classeur. Couvrir les lignes existantes et futures. Relire les montants affichés et sous-jacents : valeurs et formules inchangées, montants affichés égaux aux euros source, absence d’arrondi et d’échelle en millions.
3. Synchroniser uniquement la connexion Airbyte de `src_gsheet_films`. Attendre son succès. Vérifier dans `raw.films` la population, les euros exacts pour toutes les années et les exemples ci-dessous. Les autres colonnes, notamment les dates, doivent rester identiques.
4. Exécuter `dbt build --select +tag:phase2` avec le nouveau code : cette sélection reconstruit aussi le staging CNC et les dépendances. Vérifier les erreurs et avertissements ; ne pas relancer la collecte Allociné.
5. Effectuer les contrôles ci-dessous en SQL puis dans Metabase avec cache désactivé. Réactiver les déclenchements seulement après validation. Documenter commit, job Airbyte, run dbt, date et résultats dans l’issue #43 avant clôture.

Une erreur à n’importe quelle étape maintient les déclenchements suspendus jusqu’à rétablissement d’un couple source/dbt cohérent. La simple fusion de la PR ne clôture pas l’issue.

## Contrôles de publication

À sources inchangées, vérifier les valeurs numériques exactes suivantes :

| Visa | Film | Budget en euros | Tranche attendue |
| --- | --- | ---: | --- |
| 132030 | Hippocrate | 3 785 000 | 2 à 5M€ |
| 143380 | Le ciel attendra | 3 945 000 | 2 à 5M€ |
| 121960 | Chic ! | 8 175 000 | 5 à 10M€ |
| 147329 | Deux fils | 4 996 371 | 2 à 5M€ |
| 148355 | Convoi exceptionnel | 4 995 717 | 2 à 5M€ |
| 158285 | Vermines | 4 998 106 | 2 à 5M€ |

Comparer tous les budgets publiés aux valeurs numériques du GSheet, et pas uniquement au legacy ou aux exemples. Reprendre aussi la comparaison des 2 667 films de l’audit, sous réserve de réconciliation des changements de sources depuis le 13 novembre. Pour les autres films, notamment les agréments antérieurs à 2013, aucune régression n’est attendue.

Contrôler la conservation des films et crédits, l’unicité des clés, l’absence de nouveaux budgets nuls et l’absence de multiplication par un million. Recalculer les statistiques avec les mêmes visas, dates, postes, genres et filtres : distinguer les effets du budget des autres écarts legacy/dbt. Vérifier les questions Metabase qui exploitent budgets moyens et tranches sans modifier leurs définitions.

## Retour arrière

Maintenir les déclenchements suspendus. Restaurer les anciens formats de `DEVIS` sans réécrire les valeurs numériques ni les formules ; restaurer simultanément l’ancien commit dbt avec sa conversion conditionnelle. Resynchroniser la connexion `films`, reconstruire les dépendances avec cet ancien code et vérifier que le jeu publié retrouve son état antérieur. Ne pas rétablir uniquement le multiplicateur sur une source encore en euros exacts.

Si les valeurs source ont évolué depuis la préparation, réconcilier ces modifications avant retour arrière. Ne pas restaurer une version complète du classeur qui effacerait des corrections indépendantes. L’issue reste ouverte puisque ce retour arrière réintroduit la perte de précision connue.

## Vérifications automatisées

`tests/ingestion/test_dbt_manual_recovery.py` exécute les vrais SQL de staging et d’intermediate dans des transactions PostgreSQL en lecture seule, avec des fixtures en CTE. Le test des budgets couvre les années avant/après 2013 et l’année absente, les séparateurs d’espaces, virgule/point, centimes, blancs/nuls, zéro, les trois tranches erronées et les seuils 2/5/10/20 M€. Il vérifie aussi le type PostgreSQL `numeric`.

Depuis la racine, avec un accès SSH PostgreSQL autorisé :

```bash
DBT_TEST_SSH=cinestats-db DBT_TEST_DATABASE=cinestats-5050-db \
  .venv-visa-matching/bin/python -m unittest discover \
  -s tests/ingestion -p test_dbt_manual_recovery.py -v
```

Sans `DBT_TEST_SSH`, cette suite est ignorée ; son succès ne doit pas être annoncé sur la seule base de tests ignorés. Les fixtures ne constituent pas une vérification des montants publiés en production.
