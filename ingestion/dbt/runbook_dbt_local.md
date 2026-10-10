# Runbook dbt local : debug et documentation

## Metadata du document

**Owner:** Joel Teixeira

**Last reviewed:** 2026-10-10

**Status:** active

## Historique du document

| #   | Date       | Author         | Observations                                                          |
| --- | ---------- | -------------- | --------------------------------------------------------------------- |
| 1   | 2026-05-22 | Joel Teixeira | Guide dev pour lancer `dbt test` hors container                      |
| 2   | 2026-10-10 | Joel Teixeira | Renommage, ajout de macOS et de dbt Docs, alignement des versions sur le worker Prefect |

## Objectif

Exécuter dbt sans conteneur sur macOS (Mac Apple Silicon ou Intel) et Windows via WSL2 : vérifier la connexion, lancer les tests et consulter la documentation avec son graphe de dépendances.

## Prérequis

1. Sur Mac : terminal macOS avec Python 3.12 et son module `venv` disponibles. Sur Windows : terminal WSL2 Ubuntu/Debian avec ces mêmes outils.
2. Dépôt cloné et terminal ouvert à sa racine.
3. Fichier `ingestion/.env` configuré avec `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` et `DBT_USER_POSTGRES_PASSWORD`. Définir `POSTGRES_SSLMODE` selon le serveur ; le profil utilise `disable` par défaut. `DBT_THREADS` est facultatif (défaut : `4`).
4. Accès réseau à PostgreSQL et droits de lecture du compte `dbt_user` sur les relations concernées. Le profil utilise ce compte explicitement.

Le fichier [profiles/profiles.yml](profiles/profiles.yml) définit la connexion. Ne pas versionner `.env`, les secrets ou le contenu de `.venv-dbt`.

## Créer l'environnement sur macOS ou WSL2

Ces commandes fonctionnent dans Bash et Zsh. Elles créent l'environnement dédié `ingestion/dbt/.venv-dbt`. Les versions dbt correspondent au [Dockerfile du worker Prefect](../prefect/Dockerfile).

```bash
cd ingestion/dbt
python3.12 -m venv .venv-dbt
source .venv-dbt/bin/activate
python -m pip install --upgrade pip
python -m pip install "dbt-core==1.11.7" "dbt-postgres==1.10.0" "python-dotenv[cli]>=1.0"

python --version
command -v dbt
dbt --version
```

`command -v dbt` doit pointer vers `ingestion/dbt/.venv-dbt/bin/dbt`. Si l'environnement existe déjà, l'activer sans le recréer. Pour les sessions suivantes, revenir dans `ingestion/dbt`, puis exécuter `source .venv-dbt/bin/activate`.

Toutes les commandes suivantes s'exécutent depuis `ingestion/dbt`, avec cet environnement activé. Le préfixe `python -m dotenv -f ../.env run --` charge les variables de `ingestion/.env` pour chaque commande, sans interpréter le fichier comme un script shell. Par défaut, ses valeurs remplacent les variables homonymes du terminal pour cette commande.

## Vérifier la configuration et déboguer

```bash
python -m dotenv -f ../.env run -- dbt debug --profile ric --project-dir . --profiles-dir profiles
python -m dotenv -f ../.env run -- dbt parse --profile ric --project-dir . --profiles-dir profiles
```

`dbt debug` vérifie notamment la connexion PostgreSQL. `dbt parse` vérifie le projet et ses références sans construire les modèles.

Pour lancer les tests sur les relations déjà présentes en base :

```bash
python -m dotenv -f ../.env run -- dbt test --profile ric --project-dir . --profiles-dir profiles
```

Cette commande ne construit pas les modèles manquants. Pour limiter les tests à une phase, ajouter `--select tag:phase1` ou `--select tag:phase2`. Ces sélections ne couvrent pas tous les modèles intermédiaires et finaux ; voir le [README dbt](README.md).

Pour obtenir les détails d'un échec :

```bash
python -m dotenv -f ../.env run -- dbt --debug test --profile ric --project-dir . --profiles-dir profiles
```

Consulter `logs/dbt.log` et, pour les résultats de tests, `target/run_results.json`. Masquer les informations de connexion avant de partager les logs.

## Générer et consulter dbt Docs

```bash
python -m dotenv -f ../.env run -- dbt docs generate --profile ric --project-dir . --profiles-dir profiles
python -m dotenv -f ../.env run -- dbt docs serve --project-dir . --profiles-dir profiles --host 127.0.0.1 --port 8080 --no-browser
```

Ouvrir [http://localhost:8080](http://localhost:8080) dans le navigateur du Mac ou de Windows. Le serveur reste actif dans le terminal ; `Ctrl+C` l'arrête.

`docs generate` compile le projet et interroge les métadonnées PostgreSQL pour produire notamment `target/manifest.json`, `target/catalog.json` et `target/index.html`. Cette commande ne lance pas `dbt build`. Régénérer les fichiers après une modification des modèles ou de leurs descriptions.

Dans dbt Docs, utiliser l'icône de graphe en bas à droite pour afficher les dépendances entre sources et modèles. Le graphe représente les relations déclarées dans dbt ; il ne décrit pas à lui seul les étapes Airbyte ou scraping exécutées par Prefect.

## Dépannage macOS et WSL2

| Symptôme | Vérification ou action |
| --- | --- |
| `python3.12: command not found` | Installer Python 3.12 pour le système utilisé, puis rouvrir le terminal. Sur WSL2, installer Python dans Linux. |
| `dbt: command not found` | Activer `.venv-dbt` et vérifier `command -v dbt`. Installer les dépendances avec `python -m pip` dans cet environnement. |
| Erreur d'architecture sur Mac (`arm64` / `x86_64`) | Utiliser un Python adapté au terminal et recréer l'environnement avec ce Python. Ne pas réutiliser un environnement copié depuis une autre machine ou architecture. |
| Variable d'environnement manquante | Vérifier les noms de variables dans `../.env` et utiliser le préfixe `python -m dotenv -f ../.env run --`. |
| Connexion refusée ou délai dépassé | Vérifier hôte, port, accès réseau/VPN, pare-feu et disponibilité PostgreSQL. Avec WSL2 et PostgreSQL hébergé côté Windows, vérifier l'adresse accessible depuis WSL2 plutôt que supposer `localhost`. |
| `Operation not permitted` dans un environnement restreint | Autoriser l'accès réseau ou l'écoute locale dans cet environnement, ou lancer la commande depuis un terminal local disposant de ces droits. |
| Échec SSL ou authentification | Vérifier `POSTGRES_SSLMODE`, le mot de passe dbt et les règles d'accès PostgreSQL. |
| Relation absente pendant les tests | Vérifier que les modèles concernés ont été construits dans la base ciblée. `dbt test` et `docs generate` ne les construisent pas. |
| Port `8080` déjà occupé | Arrêter l'ancien serveur ou utiliser `--port 8081`, puis ouvrir `http://localhost:8081`. |
| Page vide ou fichiers Docs absents | Vérifier la réussite de `docs generate` et servir le même projet avec le même répertoire `target`. |

Le chargement via `python-dotenv` accepte les fins de ligne Windows : aucune modification de `.env` avec `sed` n'est nécessaire sur Mac ou WSL2.

## Documentation associée

- [README dbt](README.md) : modèles, tags et permissions.
- [README ingestion](../README.md) : orchestration et état du pipeline.
