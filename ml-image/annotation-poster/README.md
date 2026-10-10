# Annoter les affiches de films

**Owner:** Data Team DataForGood
**Dernière révision:** 2026-10-10
**Status:** actif

Outil local indépendant du site Cinestats. Il affiche les prédictions de visages, genre perçu et tranche d’âge apparente, puis conserve les corrections humaines dans un jeu de référence. Aucune écriture dans la base RIC. L’inférence reste séparée de l’éditeur.

## Démarrer avec Docker

Prérequis : Docker avec Compose, réseau pour construire les images et espace pour les médias. Depuis la racine du dépôt :

```bash
cd ml-image/annotation-poster
cp .env.example .env
docker compose --env-file .env up --build -d
docker compose --env-file .env ps
```

Ouvrir **http://localhost:3010**. L’interface et son API sont propres à cet outil ; aucun composant du site Cinestats n’est lancé. Le port est lié à l’interface locale uniquement. Cet outil ne comporte pas d’authentification et n’est pas prévu pour une exposition publique.

Les versions Python/Node, les dépendances Python et le verrou pnpm sont figés. Aucun GPU ni poids ML n’est requis pour annoter. Les images Docker ne contiennent ni credentials, ni médias, ni poids.

`ANNOTATION_PORT` permet de changer le port local dans `.env`. Après modification de la configuration ou mise à jour du code, relancer `docker compose --env-file .env up --build -d`.

Les dossiers `data/` persistent après arrêt ou reconstruction. Sauvegarder ce dossier avec l’outil arrêté ; le recopier au même emplacement pour restaurer. Ne pas versionner ces données.

```bash
docker compose --env-file .env logs --tail 50
docker compose --env-file .env down
```

## Retrouver une affiche par identifiant Allociné

Renseigner `ANNOTATION_DATABASE_URL` dans `.env` avec une connexion PostgreSQL **en lecture seule**, accessible depuis Docker. Exemple de format, avec valeurs fictives :

```text
ANNOTATION_DATABASE_URL=postgresql+psycopg://lecteur:mot_de_passe@hote:5432/base
```

La base doit exposer `public.ric_films` et `public.ric_posters`. Pour un PostgreSQL sur la machine hôte sous Docker Desktop, utiliser un hôte accessible depuis le conteneur plutôt que `localhost`. Un staging privé nécessite une connexion réseau ou un tunnel configuré séparément ; aucun accès staging n’est embarqué.

Saisir l’identifiant Allociné puis **Rechercher en base**. L’outil recherche le film, récupère l’URL `ric_posters.image_base64` et télécharge une copie locale. Les transactions SQL sont explicitement en lecture seule. En cas de film ou affiche absent, ambiguïté ou indisponibilité, l’interface affiche une erreur.

`ANNOTATION_IMAGE_HOSTS` contient les hôtes HTTPS autorisés, séparés par des virgules. Adapter cette liste côté serveur si les affiches viennent d’un autre fournisseur. Les valeurs Base64 historiques ne sont pas prises en charge par cet import ; importer alors une image locale décodée.

Une préparation locale avec le même identifiant Allociné est réutilisée avant toute requête en base. Une réouverture ne remplace ni image ni corrections. **La recherche ne lance pas l’IA** : sans prédictions préparées, l’interface l’indique et permet une annotation manuelle.

## Préparer des prédictions

Depuis ce dossier, importer une image et une liste JSON de prédictions :

```bash
docker compose run --rm --no-deps \
  -v /chemin/vers/mes-fichiers:/input:ro annotation-api \
  python -m api.importer --root /data \
  --id allocine-259157 --allocine-id 259157 --title 'Mon film' \
  --image /input/poster.jpg --predictions /input/predictions.json
```

Format d’une prédiction ; les coordonnées sont en pixels dans l’image originale :

```json
[{"id":"p1","bbox":[10,20,50,80],"gender":"female","age_range":"70+","detection_confidence":0.87,"provenance":"trailer_match"}]
```

Genre : `female`, `male`, `unknown`. Âge : `0-2`, `3-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+`, `unknown`. Un attribut absent reste non renseigné. `unknown` signifie indéterminable ; il n’est jamais converti en âge zéro. Omettre `--predictions` pour partir d’une image sans prédictions.

`--metadata fichier.json` permet de renseigner `run_id`, `code_version`, `weights` et `parameters`. Sans information, ces champs restent nuls ; aucune version n’est inventée. Les imports sont signalés comme déjà filtrés. Un identifiant existant est refusé : utiliser un nouveau dossier pour une autre exécution.

Pour convertir un **pickle local de confiance**, utiliser `--trusted-pickle` à la place de `--predictions`, dans l’environnement ML qui possède NumPy. Depuis la racine du dépôt :

```bash
PYTHONPATH=ml-image/annotation-poster ml-image/.venv/bin/python -m api.importer \
  --root ml-image/annotation-poster/data \
  --id allocine-259157 --allocine-id 259157 --title 'Mon film' \
  --image /chemin/poster.jpg --trusted-pickle /chemin/poster_predictions.pkl
```

Aucun pickle ne passe par le navigateur. Ne charger que des fichiers produits localement et de confiance : le format peut exécuter du code.

La pipeline ML peut aussi exporter avant agrégation CSV et suppression des médias. Depuis `ml-image/`, avec son environnement et ses poids installés :

```bash
ANNOTATION_EXPORT_DIR="$PWD/annotation-poster/data" ANNOTATION_RUN_ID=essai-01 \
  .venv/bin/python main.py --source /chemin/films.csv --mode infer --istart 0 --istop 1
```

Cet export conserve les boîtes retenues, le genre et l’âge issus des associations avec la bande-annonce. Il reste **filtré** : les détections rejetées ne sont pas reconstituées. Les empreintes concernent les poids `.pt` dans `ml-image/models/` ; les poids téléchargés dans les caches externes ne sont pas encore inventoriés. L’inférence elle-même n’est pas conteneurisée par ce Compose.

## Relire et exporter

1. Sélectionner un visage. Corriger sa boîte par déplacement, poignée ou coordonnées ; corriger genre et âge séparément.
2. Valider chaque champ, ou utiliser **Tout valider pour ce visage**. Supprimer les fausses détections ; elles restent traçables.
3. Ajouter les visages oubliés en dessinant une boîte. Utiliser zoom, déplacement de l’image et annuler/rétablir si nécessaire.
4. Renseigner l’annotateur. Confirmer la relecture de toute l’affiche, puis **Valider l’affiche**.
5. Télécharger **la référence et le bilan**. Les comptes de corrections ne sont pas des scores d’exactitude.

La sauvegarde est automatique. Une erreur reste visible ; un conflit entre onglets impose de recharger. Toute correction après validation remet le dossier en brouillon. Une affiche sans visage peut être validée avec une référence vide.

Chaque dossier contient `manifest.json`, `image.jpg`, `predictions.json` (intact), `review.json` (révision et décisions), puis `reference.json` lors de l’export. Une nouvelle sauvegarde invalide l’export précédent sur disque ; les téléchargements déjà effectués gardent leur numéro de révision. Une image remplacée est refusée grâce à son empreinte.

## Dépanner

| Symptôme | Action |
| --- | --- |
| Liste vide | Importer une affiche ; aucun média n’est livré avec le dépôt |
| Recherche en base non configurée | Renseigner `ANNOTATION_DATABASE_URL`, puis recréer les conteneurs avec `up -d` |
| Base indisponible | Vérifier connexion, tunnel éventuel et accès depuis Docker ; `localhost` dans le conteneur désigne ce conteneur |
| URL d’affiche refusée | Vérifier le format HTTPS et `ANNOTATION_IMAGE_HOSTS` ; Base64 nécessite un import local |
| Conflit de sauvegarde | Utiliser **Recharger / abandonner** ; les modifications de l’autre onglet restent conservées |
| Validation impossible | Relire boîte, genre et âge de chaque visage, puis confirmer la relecture complète |
| Image modifiée | Préparer un nouveau dossier ; ne pas remplacer l’image d’une référence existante |

Les journaux se consultent avec `docker compose --env-file .env logs --tail 50`.

## Développer et vérifier

Depuis la racine du dépôt :

```bash
uv venv ml-image/annotation-poster/.venv
uv pip install --python ml-image/annotation-poster/.venv/bin/python \
  -r ml-image/annotation-poster/requirements.txt pytest==7.4.4 playwright==1.58.0
PYTHONPATH=ml-image/annotation-poster ml-image/annotation-poster/.venv/bin/python \
  -m pytest ml-image/annotation-poster/tests -q
```

Dans `web/` : `pnpm install --frozen-lockfile`, `pnpm type-check`, `pnpm build`.
Pour le parcours navigateur, démarrer Compose puis, depuis la racine :

```bash
ml-image/annotation-poster/.venv/bin/python -m playwright install chromium
PYTHONPATH=ml-image/annotation-poster ml-image/annotation-poster/.venv/bin/python \
  ml-image/annotation-poster/tests/browser_smoke.py
```

Le test crée puis supprime uniquement son dossier `browser-fixture`. Il vérifie l’export, l’invalidation après correction, annuler/rétablir, les coordonnées au zoom, l’ajout, la suppression/restauration et la reprise. `PLAYWRIGHT_CHROMIUM_EXECUTABLE` permet d’utiliser un Chromium déjà installé.

Pour lancer hors Docker : depuis ce dossier, `ANNOTATION_ENABLED=true ANNOTATION_DATA_DIR="$PWD/data" .venv/bin/python -m uvicorn api.app:app --host 127.0.0.1 --port 5010`, puis depuis `web/`, `ANNOTATION_ENABLED=true pnpm dev`. Les routes sont désactivées sans cette variable.

## Vérifications réalisées

Le 10 octobre 2026 : construction et démarrage Docker sur hôte macOS ARM64, contrôle TypeScript, 15 tests API/import/export et parcours navigateur Chromium réussis. Le test historique d’export ML passe aussi. Les tests de recherche SQL utilisent une connexion simulée ; la connexion réelle à staging reste à configurer et à vérifier. L’inférence complète n’a pas été relancée pour cette livraison.

Une affiche locale de **Natacha, hôtesse de l’air** (Allociné **259157**) a été préparée avec les sept prédictions du test ML antérieur. Elle est disponible sur la machine de développement, dans `data/allocine-259157/`, mais n’est pas distribuée avec le dépôt.

## Références

- [Spécification fonctionnelle](../../docs/specifications/ml-image-annotation-affiches-implementation.md)
- [Module ML](../README.md)

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-10 | Joel Teixeira | Outil autonome annotation-poster : installation Docker, import Allociné, correction, export et vérifications. |
