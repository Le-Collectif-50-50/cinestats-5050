# Guide de finalisation de dbt

**Resonsable** Data Team DataForGood
**Dernière révision:** 2026-10-10
**Status:** active

## Historique du document

| # | Date | Author | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-10 | Joel Teixeira | Rédaction du document. Guide de finalisation de l'implementation dbt |

## Objectif et liberté de conception

Produire des données fiables et reproductibles. Elles doivent alimenter frontend et Metabase.

**Le développeur choisit librement les noms des tables et champs.** La structure peut aussi évoluer. Une table historique n'impose pas un équivalent individuel.

Les noms cités désignent le code audité. Ils servent uniquement à localiser les problèmes. Les renommages doivent être répercutés dans les dépendances, tests et consommateurs concernés. L'API peut conserver son contrat via une adaptation backend.

## Point de départ

Observations du **10 octobre 2026**, en lecture seule. Code audité : `117234f66afcbd36a95da218a62f037d1177c9fb`.

| Environnement | État utile pour l'implémentation |
| --- | --- |
| Staging data (`ingestion/.env`) | Sept tables finales présentes ; 5 539 films stockés. Le SQL versionné ne reproduit pas cet état. Tables historiques dans `raw_legacy`. |
| Production (`cinestats-db`) | Quinze tables historiques dans `public` ; 6 618 films. Sources brutes présentes, mais aucun final dbt. Seulement deux vues dans `staging`. |

Le staging data n'est pas nécessairement la preview applicative. Leur identité n'a pas été vérifiée. Aucun build dbt n'a été exécuté. Les questions Metabase restent à inspecter.

## 1. Définir les données à publier

Conserver cette couverture fonctionnelle, indépendamment du nommage :

| Usage frontend | API | Données nécessaires | Travail restant |
| --- | --- | --- | --- |
| Recherche | `/search` | Films, affiches, réalisateurs | Fiabiliser films/crédits ; publier les affiches |
| Fiche film | `/films/{id}` | Métadonnées, genres, pays, crédits, récompenses, médias et métriques | Compléter les domaines manquants ci-dessous |
| Fiche festival | `/festivals/{id}?year=…&award=…` | Festivals, prix, nominations, films et réalisateurs | Publier les données festivals/prix/nominations |
| Statistiques | `/metabase/iframe-url` puis Metabase | Jeux de données utilisés par les questions Metabase | Inventorier les questions et leurs dépendances |

À compléter : pays, festivals, prix, nominations, affiches, bandes-annonces et prédictions des personnages sur ces deux médias. Une reprise historique peut constituer une première étape. Définir alors sa source et son actualisation.

**Validation :** chaque usage dispose d'une source publiée. Toute exclusion temporaire est explicitée et validée.

## 2. Stabiliser identifiants et règles métier

- [ ] Choisir des identifiants stables et cohérents. Prévoir le lien avec les anciens IDs. L'API actuelle attend des entiers ; dbt génère des UUID.
- [ ] Prévoir les films sans visa CNC. La production en contient 770.
- [ ] Définir la priorité CNC/Allociné/corrections par champ.
- [ ] Valider les changements de sens ou type : ASR texte → booléen, rang → catégories, diffuseurs → tableau.
- [ ] Choisir les codes métier des rôles. L'API filtre aujourd'hui sur `actor`/`director` ; dbt produit `Acteur`/`Réalisateur`.
- [ ] Valider la définition du financement français : premier contributeur ou participation ≥ 50 %.

**Validation :** décisions documentées et consommateurs identifiés. Aucun changement métier masqué par un renommage.

## 3. Corriger les transformations

| Problème localisé dans le code audité | Résultat attendu |
| --- | --- |
| `fnl_film_credits` utilise `chr.allocine_id`, absent en amont | Jointure valide ; crédits reliés aux films |
| `fnl_film_country_budget_allocation` utilise des colonnes absentes (`id`, `fix.cnc_visa`, `fix.country_name`) | Projection et corrections cohérentes avec les entrées |
| Intermédiaires MUBI : jointure entier/texte | Types d'identifiants compatibles |
| `int_credit_holders_role` calcule les IDs sociétés depuis `full_name=NULL` | Identifiants sociétés stables et non NULL |
| Films : matching incomplet et Allociné non dédupliqué | Une ligne par film ; exclusions justifiées |
| `stg_cnc_films` supprime les espaces avant découpage | Listes de diffuseurs/rangs correctement séparées |
| `stg_fix_film_credits` convertit le même ID en UUID et BIGINT | Corrections valides acceptées |
| Corrections rôles/crédits/film-genres non raccordées aux finals | Corrections appliquées aux sorties concernées |
| Financement français calculé avant corrections d'allocations | Indicateurs dérivés recalculés après correction |

Repère de non-régression : sur le staging audité, le SELECT film versionné produit **5 390 lignes pour 5 328 films distincts**. Il exclut **211 visas CNC sans matching**. Ces écarts doivent être résolus ou expliqués.

**Validation :** tous les modèles du périmètre s'exécutent. Le résultat ne dépend pas d'anciennes vues oubliées.

## 4. Tester et automatiser la publication

- [ ] Aligner les tests YAML sur les colonnes réellement publiées.
- [ ] Tester unicité, valeurs obligatoires et relations entre entités.
- [ ] Tester la propagation d'une correction métier.
- [ ] Contrôler couverture des films et écarts de volumes. Documenter les exclusions et regroupements attendus.
- [ ] Reconstruire en staging depuis les sources déclarées. Comparer aux tables existantes ; expliquer les différences.
- [ ] Vérifier qu'une relance n'ajoute aucun doublon.
- [ ] Étendre l'orchestration Prefect aux modèles finaux et tests. Les sélections actuelles `phase1`/`phase2` ne les couvrent pas.

**dbt est finalisé pour le périmètre retenu lorsque le pipeline reconstruit toutes les sorties attendues et passe ces contrôles.**

## 5. Préparer la bascule des consommateurs

Cette étape suit la validation de dbt.

- [ ] Adapter les modèles ORM et repositories aux sorties choisies. Changer seulement `DATABASE_SCHEMA` ne suffit pas.
- [ ] Préserver les réponses API ou adapter explicitement le frontend. Vérifier aussi les liens existants utilisant les anciens IDs.
- [ ] Adapter les questions, jointures et filtres Metabase.
- [ ] Préparer droits et index utiles. En production, `app_ro` n'a pas accès au schéma `fnl`.
- [ ] Recetter recherche, films, festivals et statistiques.
- [ ] Prévoir un retour aux lectures historiques avant bascule.

**Bascule prête :** fonctionnalités validées sur les nouvelles données, accès vérifiés et écarts métier acceptés.

## Fichiers de référence

- [Modèles dbt](../../ingestion/dbt/models/) et [périmètre d'exécution](../../ingestion/dbt/README.md).
- [Orchestration Prefect](../../ingestion/prefect/flows.py).
- [Recherche](../../backend/use_cases/search_films.py), [fiche film](../../backend/use_cases/get_film_details.py), [fiche festival](../../backend/use_cases/get_festival_details.py).
- [Modèles historiques](../../database/models/) et [règles métier historiques](../../backend/entities/film_entity.py).
