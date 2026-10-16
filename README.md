# Révéler les Inégalités dans le Cinéma (RIC)

**Resonsable** Data Team DataForGood
**Dernière révision:** 2026-10-10
**Status:** active

Projet Data For Good et Collectif 50/50 : informer le grand public et les institutions sur les inégalités de genre dans le cinéma français.

## Architecture et documentation

L'application associe Next.js, FastAPI et PostgreSQL (SQLAlchemy/Alembic).
Lire uniquement le guide du composant concerné, puis suivre ses références selon la tâche.

| Dossier | Rôle et documentation |
| --- | --- |
| `frontend/` | [Interface Next.js : installation et développement](frontend/README.md) |
| `backend/` | [API FastAPI : lancement, accès aux données et tests](backend/README.md) |
| `database/` | [PostgreSQL : modèles, migrations, seeds et données historiques](database/README.md) |
| `ingestion/` | [Airbyte, dbt, Prefect et scraping : état actuel, configuration et architecture](ingestion/README.md) |
| `ml-image/` | [Analyse d'images et bandes-annonces : installation et modèles](ml-image/README.md) |
| `infra/`, `scripts/`, `.github/` | [Infrastructure et déploiement applicatif](docs/DEPLOYMENT.md), [exploitation de la stack data](docs/runbooks/stack-data.md) |
| `docs/` | Architecture, spécifications et runbooks, référencés depuis les guides ci-dessus |

## Démarrer en local

Prérequis : Git et les outils du composant choisi. Voir le [guide d'installation](docs/repo-setup.md) pour Docker Compose et Poetry.

Interface, avec Node.js et pnpm installés, depuis la racine :

```bash
cd frontend
pnpm install
pnpm dev
```

Interface : `http://localhost:3000`. Configurer l'API et la base selon leurs guides pour accéder aux données.
Pour Docker, renseigner `.env` depuis [.env.example](.env.example), puis utiliser [docker-compose.yaml](docker-compose.yaml).
L'ingestion et le ML ont leurs propres prérequis et commandes.

## Contribuer et vérifier

Agents : [consignes communes](AGENTS.md), importées par [CLAUDE.md](CLAUDE.md).
Documentation : suivre le [standard documentaire](docs/repo-documentation-guidelines.md).

Pour le code Python, depuis la racine :

```bash
poetry install --with dev
poetry run pre-commit run --all-files
poetry run python -m pytest tests
```

Relancer `poetry install --with dev` après une modification de `poetry.lock`.
[Tox](tox.ini) fournit aussi un environnement de test (`poetry run tox -vv`).
Pour le frontend, depuis `frontend/` après installation : `pnpm type-check` et `pnpm build`.

## Déployer et dépanner

Les PR ciblent `main`. Pour déployer, suivre le [runbook de promotion](docs/runbooks/deploiement-promotion-preview-production.md) : validation en `preview`, puis promotion en `production`.

- Application, configuration des environnements et rollback : [guide de déploiement](docs/DEPLOYMENT.md).
- Ingestion, connexions Airbyte/dbt/PostgreSQL : [runbook de setup et dépannage](docs/runbooks/ingestion-runbook-infra-setup-dbt-core-airbyte-remote-postgres.md).
- Exploitation du VPS data : [runbook stack data](docs/runbooks/stack-data.md).

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-07 | Joel Teixeira | Révision post implementation module ingestion |
| 2 | 2026-10-09 | Joel Teixeira | Ajout du guide de promotion preview vers production |
| 3 | 2026-10-10 | Joel Teixeira | Vue d'ensemble condensée, parcours local et liens ciblés vers les guides de travail et d'exploitation. |
