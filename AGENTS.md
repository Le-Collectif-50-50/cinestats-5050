# Consignes pour les agents

**Resonsable** Data Team DataForGood
**Dernière révision:** 2026-10-10
**Status:** active

## Contexte et lecture ciblée

RIC révèle les inégalités de genre et raciales dans le cinéma français.
Ce fichier est la source commune des consignes ; `CLAUDE.md` l'importe.
Lire le [README](README.md) pour la vue d'ensemble, puis uniquement les documents utiles à la tâche. Suivre leurs liens si nécessaire, sans charger toute la documentation.

| Zone concernée | Point d'entrée à lire |
| --- | --- |
| Interface Next.js | [frontend/README.md](frontend/README.md) |
| API FastAPI | [backend/README.md](backend/README.md) |
| PostgreSQL, modèles, migrations, seeds | [database/README.md](database/README.md) |
| Airbyte, dbt, Prefect, scraping actif | [ingestion/README.md](ingestion/README.md) |
| Données et scraping historiques | [database/data/README.md](database/data/README.md) |
| Analyse d'images et bandes-annonces | [ml-image/README.md](ml-image/README.md), puis [architecture ML](docs/architecture/ml-image-architecture-description-pipeline-phase-1.md) |
| Déploiement application, CI, infrastructure | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Exploitation du VPS data | [runbook stack data](docs/runbooks/stack-data.md) |
| Création ou restructuration documentaire | [standard documentaire](docs/repo-documentation-guidelines.md) |

## Règles de travail

- Vérifier le code et la configuration : une architecture cible ou un document `draft` ne prouve pas une implémentation. Pour l'ingestion, distinguer état actuel, cible et placeholders.
- Le backend utilise encore les tables `ric_*` ; ne pas supposer une bascule vers dbt. Distinguer les collectes historiques de `database/data/` des jobs de `ingestion/`.
- Vérifier les prérequis système et les poids des modèles avant toute exécution ML, et la base cible avant une migration ou un seed.
- Garder les changements ciblés. Ne pas versionner de secrets, credentials ou données sensibles.
- Mettre à jour la documentation concernée dans la même PR. Rédiger en français ; conserver les champs `Owner`, `Dernière révision`, `Status` en tête et l'historique ci-dessous au format `#`, `Date`, `Auteur`, `Observations`.
- Exécuter les vérifications adaptées à la zone modifiée, selon le README et les configurations du composant. Indiquer les vérifications effectuées et les limites restantes.
- Maintenir les consignes communes ici ; conserver `CLAUDE.md` comme simple import. Placer les procédures détaillées dans les sous-documents et les référencer.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-07 | Joel Teixeira | Initial implementation |
| 2 | 2026-10-10 | Joel Teixeira | Consignes condensées et orientation documentaire par tâche ; source commune aux agents. |
