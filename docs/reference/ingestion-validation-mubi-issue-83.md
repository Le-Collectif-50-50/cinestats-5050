# Validation du flux Mubi CNC — issue 83

**Owner:** Joel Teixeira
**Dernière révision:** 2026-11-16
**Status:** actif

Le flux Mubi CNC est déployé et validé en production le 16 novembre 2026.
Les deux actions Metabase, par lot et par visa avec forçage, ont terminé leurs
parcours Airbyte → collecte → dbt. Le [dashboard Mubi](https://metabase.cinestats5050.fr/dashboard/12)
est publié dans Operations. Le crawler global reste différé. La
[PR #84](https://github.com/Le-Collectif-50-50/cinestats-5050/pull/84) conserve le
code livré ; sa fusion dans `main` reste distincte de cette livraison autorisée.

## Vérifications réalisées

- Tests ingestion : 199 réussis, 27 ignorés, 10 sous-tests réussis. Les exclusions
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

## Mesure instrumentée complémentaire

Un second comparatif a isolé `Page.goto`, ouverture/fermeture de session et
fetch complet, sur les mêmes trois pages et le même Browserless, après les
runs métier. Le candidat utilisait aussi l’attente explicite de la payload.

| Mesure, secondes | Référence `networkidle` | Candidat DOM + ressources filtrées |
| --- | --- | --- |
| Total, ouverture et fermeture comprises | 51,686 | 37,943 |
| Ouverture de session | 1,049 | 1,113 |
| Fermeture de session | 0,184 | 0,198 |
| Somme des trois navigations `goto` | 15,804 | 2,641 |
| Somme des trois fetchs, temporisations comprises | 50,452 | 36,632 |

Les trois empreintes des données parsées sont identiques entre variantes et
avec le premier comparatif. Aucun blocage, timeout ni erreur n’a été observé ;
le chemin de retry n’est donc pas mesuré par cet essai. La réduction totale est
de **26,6 %** dans ce second passage, contre **33,4 %** dans le premier. Les
attentes de courtoisie étant aléatoires, ces deux petites paires ne permettent
pas d’annoncer un gain fixe sur le catalogue ou sur Airbyte/dbt. L’ouverture et
la fermeture sont comparables ; l’attente de navigation explique le principal
gain mesuré.

## Livraison effectuée

Le runtime livré est `b2646ba`, six fichiers ciblés : navigateur partagé,
connecteur/CLI CNC, flows, démarrage worker et vue ops. Le marqueur
`~/cinestats-data/ISSUE_83_REF` et les empreintes dans
`~/cinestats-data/backups/issue-83-b2646ba/sha256-after.txt` identifient cette
livraison partielle. `DEPLOYED_REF` conserve son rôle de marqueur de la copie
globale antérieure ; il ne décrit pas à lui seul tous les fichiers actifs.

- Aucune demande métier active avant livraison. Un ancien état `Submitting` de
  poller du 9 octobre était encore visible, sans exécution métier ; il n’a pas
  été annulé arbitrairement.
- Sauvegarde préalable : `backups/issue-83-b2646ba/runtime-before.tar` et
  `sha256-before.txt`, sous `~/cinestats-data/`.
- Deux migrations appliquées avec `dbt_user`, propriétaire des tables : colonnes
  brutes `event_slug`/`event_type`, puis contraintes et verrou global de file.
  Historique conservé, aucun droit supplémentaire accordé au scraper.
- Seul le worker a été recréé. Serveur Prefect, Browserless, images et `.env`
  conservés. Les quatre déploiements sont présents ; seul le poller garde un
  calendrier. Mubi et Allociné ont une concurrence de 1 chacun.
- `ops.v_mubi_pipeline_status` construit ; le droit SELECT de
  `metabase_ops_user` est confirmé. Le premier build ciblé termine sans erreur.
- Dashboard 12 : dix questions (134 à 143), actions 4 (lot) et 5 (visa), modèle
  de file 38, collection Operations 7. Plusieurs republications ont conservé
  ces IDs et n’ont créé aucun doublon. Questions et dashboard héritent des
  permissions de leur collection ; le compte de recette peut lire et déclencher
  les actions. La clé de maintenance ne permet pas de consulter la matrice
  administrative des groupes (403) ; aucune permission de groupe n’a été modifiée.
- Les formulaires ont été soumis dans l’interface. Les filtres du dashboard
  n’ont pas prérempli ni remplacé le visa saisi dans le formulaire ciblé.
- La recette visuelle a conduit à placer état/erreur de demande avant les champs
  longs et à inclure aujourd’hui dans la période par défaut (`past7days~`). Le
  filtre initial `past7days` excluait les nouvelles collectes du jour. Ce changement
  est limité à Mubi et couvert par un test de non-régression Allociné.
- Pendant le run ciblé, une insertion Allociné de test a été refusée par
  `idx_ingestion_run_requests_global_active`. Transaction systématiquement
  annulée : aucune demande de test persistée.

## Recette métier en production

Horaires ci-dessous : Europe/Paris, 16 novembre 2026. Les bilans proviennent de
Prefect ; ils ne sont pas déduits des timestamps sans fuseau de la file partagée.

| Parcours | Visa / ID Mubi | Horaire du flow | Collecte seule | Résultat |
| --- | --- | --- | --- | --- |
| Lot limité à un film | 121213 / 31987, La blonde aux seins nus | 01:16:50 → 01:21:11 | 20,06 s | Une sentinelle `no_awards`, puis dbt réussi |
| Visa explicite, forçage Oui | 134877 / 136442, Goal of the Dead | 01:22:06 → 01:31:01 | 335,81 s | Quatre lignes de palmarès, éditions ci-dessous, puis dbt réussi |

Les deux publications terminent avec **PASS=158, WARN=6, ERROR=0, SKIP=0**.
Les six contrôles en avertissement ont les mêmes résultats entre les deux runs :
IDs absents (Allociné 218, Mubi 897, TMDB 775), un groupe d’ID partagé Mubi et un
TMDB, et contrôle de crédits en quarantaine. Ces avertissements ne constituent
pas des échecs de collecte. Ils ne sont pas supprimés par la livraison.

| Édition | Pages avec films | Lignes de films | Pages vides de terminaison |
| --- | --- | --- | --- |
| BIFFF 2014 | 1 | 2 | 1 |
| Chicago 2014 | 5 | 148 | 1 |
| NIFFF 2026 | 4 | 116 | 1 |
| Sydney 2014 | 3 | 91 | 1 |
| Total | 13 | 357 | 4 |

Ces 357 lignes ne sont pas 357 œuvres uniques du référentiel CNC : une œuvre
peut apparaître dans plusieurs éditions. Le snapshot des pages ne contient
aucun `record_hash` répété. Les quatre lignes de palmarès ne sont pas assimilées
à quatre prix remportés.

Identifiants de preuve :

- Lot : demande `e22026b2-7099-4cb4-a25a-2c4c9697e584`, flow
  `72921e23-f8c1-4b5f-bf73-e16b31584af0`, snapshot
  `49ab924d-f2dd-4ae4-a38f-49c6c1a0d1cb`, Airbyte 65.
- Visa : demande `213b84ca-e8b2-4f64-8b2c-a1ec326c71df`, flow
  `a5a4546a-3a77-4f27-a73a-746f74cf6337`, snapshot
  `a74ee1bb-5d8b-4eea-83fc-d56f73fabaf1`, Airbyte 66.

Contrôles Metabase sans cache après publication : deux demandes `success`,
une sentinelle sans palmarès pour 31987 dans le staging, quatre lignes de
palmarès pour 136442. Le programme partagé conserve les visas 134877 et 134878,
avec quatre lignes chacun dans l’intermédiaire. Aucun total d’événements ne somme
ces huit lignes : les règles de programme restent dans #82.

Couverture après recette : **6 139 lignes**, dont **897 sans ID**, **176 en attente**
et **5 066 couvertes par un succès**, correspondant à **5 065 ID Mubi distincts**.
Le lot a traité un nouvel ID ; le ciblage forcé a renouvelé un snapshot existant.
Les 176 films restant à collecter ne sont pas lancés automatiquement par cette
recette. Les identifiants manquants restent suivis dans #78.

Une relance CLI coordonnée de 134877, sans forçage, a confirmé : aucun palmarès
à traiter, aucune page d’édition à traiter, zéro ligne insérée et aucun nouveau
snapshot persistant (6,23 s, accès base compris). La reprise relit les éditions
déjà enregistrées sans les rescraper.

## Exploitation et limites

Utiliser les [procédures Mubi CNC](../../ingestion/scraping/mubi_cnc/README.md)
pour les prochains lots. Les lancements directs contournent la file Metabase :
les coordonner avec les publications en cours. Le crawl global reste sans
calendrier ni déploiement actif. Les anciennes lignes sans `event_slug` ne
permettent pas de reconstruire seules leurs éditions ; un retraitement ciblé
reste nécessaire pour ces films.

Avant toute livraison globale ultérieure, intégrer la PR #84 dans la référence
livrée pour conserver le correctif et le nouveau parcours. Les nouvelles règles
d’agrégation métier de #82 et la qualification des IDs de #78 restent séparées.

Pour revenir sur la livraison, terminer ou annuler proprement les demandes Mubi,
retirer leurs actions et arrêter leur déploiement avant de restaurer les fichiers
sauvegardés. Conserver les données collectées et les colonnes additives. Ne pas
restaurer un ancien poller tant que des demandes de type Mubi restent actives.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-16 | Joel Teixeira | Mubi CNC livré : preuves, deux parcours métier, mesures, dashboard, reprise et limites de publication. |
