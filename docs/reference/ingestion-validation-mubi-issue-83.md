# Validation du flux Mubi CNC — issue 83

**Owner:** Joel Teixeira
**Dernière révision:** 2026-11-16
**Status:** brouillon

Le candidat rétablit un parcours manuel Airbyte → Mubi CNC → dbt et prépare un
dashboard Operations avec lancement par lot ou par visa. La publication des
modifications en production et un run métier restent à effectuer. Le crawler
global reste différé.

## Vérifications réalisées

- Tests ingestion : 198 réussis, 27 ignorés, 10 sous-tests réussis. Les exclusions
  concernent principalement les tests PostgreSQL nécessitant une activation
  explicite. Sept avertissements de dépréciation préexistants dans le parseur
  Allociné restent visibles.
- Le test PostgreSQL Mubi a été exécuté séparément avec succès sur des tables
  temporaires de l’ancienne base configurée par le `.env` local. Il vérifie
  ciblage, programme partagé, reprise des éditions, remplacement par un succès
  sans palmarès, migration de file et refus de demandes inter-sources simultanées.
  Ce résultat ne prouve pas le déploiement dans la base de production courante.
- Le VPS courant utilise `cinestats-5050-db`. Les rôles scraper et dbt n’y ont pas
  le droit de créer des tables temporaires ; leurs essais ont échoué avant toute
  création. Aucun droit supplémentaire n’a été accordé.
- Un essai du candidat dans le worker courant, avec toutes les écritures et
  fonctions de création remplacées par des contrôles en mémoire, a collecté
  Mubi 136442 puis la première page de quatre éditions : BIFFF 2014, Chicago 2014,
  NIFFF 2026 et Sydney 2014. Résultat : quatre lignes de palmarès, 110 lignes de
  films, aucun statut technique d’échec, 84,55 s. La pagination était limitée à
  une page par édition pour cet essai ; ce n’est pas une validation du catalogue
  complet. Les lignes de palmarès ne constituent pas quatre prix remportés.
- Comparaison navigateur sur les trois mêmes pages : palmarès Mubi 136442,
  Cannes 2024 page 1 (36 films), Cannes 2024 page 100 (vide). Une session par
  variante, même Browserless, ouvertures/fermetures comprises : 57,15 s avant,
  38,09 s après, soit 33,4 % de réduction. Les contenus parsés ont des empreintes
  identiques. Le candidat utilise `lightweight` et `domcontentloaded` ; ce petit
  échantillon ne mesure ni Airbyte/dbt ni les cas de blocage.
- Les requêtes du futur dashboard ont été exécutées via la connexion
  Metabase de production sans cache, en intégrant la définition candidate de
  vue comme sous-requête. Les filtres visa, titre, ID Mubi combinés et la période
  relative sont validés. Un cast texte explicite du visa corrige l’incompatibilité
  entre paramètre texte Metabase et visa entier dbt.
- Instantané de couverture courant : 6 139 lignes du référentiel, dont 897 sans
  ID, 177 en attente de succès et 5 065 couvertes par un succès. Les ID partagés
  rendent ces compteurs par visa différents des compteurs d’ID distincts.
- Lint Python ciblé, syntaxe shell et vérification des espaces du diff réussis.

## Livraison et contrôle restants

1. Attendre la fin des runs métier et vérifier l’absence de demandes actives.
   Sauvegarder les fichiers déployés concernés et relever leurs empreintes.
2. Appliquer `infra/data/2026-11-16-mubi-cnc-events.sql` avec `dbt_user`, propriétaire
   des deux tables brutes vérifié sur le VPS courant. Le scraper restreint n’a
   pas le droit d’altérer ces tables. Appliquer `infra/data/ops-ingestion-table.sql` sur la base courante avec le
   propriétaire approprié. Le verrou global exige au plus une demande active ;
   ne pas supprimer des demandes pour contourner un échec de migration.
3. Livrer les fichiers navigateur, connecteur/CLI CNC, flows et démarrage worker.
   Recréer uniquement le worker selon le runbook ; conserver `.env`, images et
   secrets. Vérifier les quatre déploiements, paramètres Mubi, concurrence 1 et
   absence de calendrier de scraping. Les lancements directs contournent la file
   Metabase : les coordonner explicitement avec les autres exécutions.
4. Construire `ops.v_mubi_pipeline_status` et vérifier ses droits pour
   `metabase_ops_user`. Les colonnes `event_slug`/`event_type` du brut sont
   additives et requièrent la migration préalable sur les tables existantes.
5. Publier le dashboard avec `infra/data/metabase-mubi-review.py`, collection 7,
   modèle de file 38. Conserver son fichier d’état local, puis relancer la même
   commande pour vérifier l’absence de doublons d’objets. Vérifier permissions,
   boutons, filtres et liens dans l’interface Metabase.
6. Lancer un petit lot et un visa ciblé, suivre demande → Prefect → collecte → dbt,
   vérifier les compteurs sans cache et documenter les cas restant en échec.
   Vérifier qu’un échec technique n’est pas présenté comme une collecte publiée.
7. Renseigner les liens dashboard/PR, runs et résultats de publication avant
   clôture de #83. Les nouvelles règles d’agrégation de prix/événements restent
   dans #82 ; les identifiants manquants restent dans #78.

Pour revenir sur la livraison, terminer ou annuler proprement les demandes Mubi,
retirer leurs actions et arrêter leur déploiement avant de restaurer les fichiers
sauvegardés. Conserver les données collectées et les colonnes additives. Ne pas
restaurer un ancien poller tant que des demandes de type Mubi restent actives.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-16 | Joel Teixeira | Candidat Mubi CNC : preuves de validation et procédure de livraison restant à exécuter. |
