# Tester la pipeline image en local

**Owner:** Julien Commes
**Dernière révision:** 2026-10-10
**Status:** actif

## Périmètre

Le module analyse les visages des bandes-annonces, regroupe les détections par personnage et rapproche les visages d’une affiche des personnages détectés. Il exporte des prédictions de genre, de tranche d’âge et d’ethnie. Ces sorties sont des estimations de modèles ; le test de fonctionnement ne mesure pas leur exactitude.

La pipeline récupérée contient l’inférence et les exports. Son évaluation intégrée reste inachevée. La [description d’architecture](../docs/architecture/ml-image-architecture-description-pipeline-phase-1.md) contient encore des comportements non vérifiés, notamment le nettoyage GPU. Elle ne constitue pas une preuve d’exécution.

## Installer l’environnement CPU

Prérequis : `uv`, accès réseau et compilateur C++. Sur macOS, installer les outils de ligne de commande Xcode si `c++` est absent. Le profil local cible Python 3.11 sur macOS ARM64. Il utilise le CPU ; CUDA n’est pas requis. Les autres plateformes restent à vérifier.

Depuis la racine du dépôt :

```bash
bash ml-image/install/setup_local.sh
```

Le script crée `ml-image/.venv`, installe CMake pour compiler dlib, installe les dépendances puis vérifie le démarrage et les exports. La compilation et les téléchargements peuvent prendre plusieurs minutes.

- `requirements-local.in` : dépendances directes d’inférence.
- `requirements-local.txt` : versions résolues pour ce profil local.
- `requirements.txt` : environnement historique, distinct et non validé par cette procédure.

Le profil conserve FaceNet, NumPy 1.26 et PyTorch 2.2. Il ajoute Loguru et utilise une version de Protobuf résolue avec MediaPipe. Les deux distributions OpenCV requises par les dépendances sont fixées à la même version.

## Vérifier sans poids ni vidéo

Depuis `ml-image/` :

```bash
export XDG_CACHE_HOME="$PWD/tmp/cache"
export MPLCONFIGDIR="$PWD/tmp/matplotlib"
export YOLO_CONFIG_DIR="$PWD/tmp/ultralytics"
.venv/bin/python main.py --help
.venv/bin/python -m unittest discover -s tests -v
```

Le test d’export utilise des prédictions synthétiques. Il vérifie les chemins natifs et les valeurs CSV. Il n’exécute aucun modèle et n’écrit pas en base.

## Télécharger les poids

Depuis la racine :

```bash
source ml-image/.venv/bin/activate
bash ml-image/install/download_models.sh
python ml-image/smoke_test.py --check
```

Le script télécharge YOLO Face et FairFace dans `ml-image/models`. Les fichiers partiels portent le suffixe `.part`. Le contrôle vérifie le démarrage et la présence des fichiers, pas leur intégrité ni leur qualité.

Au 10 octobre 2026, le poids YOLO Face est récupérable depuis la [release upstream 1.0.0](https://github.com/akanametov/yolo-face). Le lien Google Drive FairFace historique et le dossier indiqué par le [projet FairFace](https://github.com/dchen236/FairFace) échouent au téléchargement automatisé dans cet environnement. Une copie de `res34_fair_align_multi_7_20190809.pt` a été fournie localement dans `ml-image/models`. Pour une nouvelle installation, obtenir ce poids séparément si le téléchargement échoue, puis relancer `--check`.

La première inférence peut aussi télécharger les poids YOLO personne, FaceNet/VGGFace2 et ResNet34 via leurs bibliothèques. Prévoir réseau et espace disque. Ne pas exécuter un téléchargement provenant d’une source non vérifiée.

## Tester un film local

Utiliser une courte vidéo contenant des visages et une affiche correspondante. Depuis la racine :

```bash
ml-image/.venv/bin/python ml-image/smoke_test.py \
  --trailer /chemin/vers/bande-annonce.mp4 \
  --poster /chemin/vers/affiche.jpg
```

Le lanceur copie les deux médias dans un répertoire unique `ml-image/tmp/smoke-*`. Les originaux restent intacts, même si la pipeline supprime les copies. Les identifiants `visa_number=1` et `allocine_id=1` sont synthétiques. Aucune insertion en base n’est effectuée.

Le test limite le traitement à un film, deux threads CPU et des lots de quatre images. Toutes les images vidéo sont toutefois chargées en mémoire. Il exige deux fichiers pickle et deux CSV non vides ; un message de succès de la pipeline seule ne suffit pas, car elle intercepte certaines erreurs.

Les CSV sont conservés sous `outputs/final_predictions/` dans le répertoire du test. Ils ne prouvent ni la qualité du regroupement ni celle des classifications.

## Échantillon staging préparé

Un accès en transaction SQL `READ ONLY` à la base `preview` a permis de sélectionner **Natacha, hôtesse de l’air** (visa 159573, Allociné 259157). L’affiche est stockée comme URL dans la colonne historique `image_base64`. Les médias et leur provenance sont conservés localement sous `tmp/staging-sample/`, ignoré par Git. La base n’a pas été modifiée.

Après disponibilité du poids FairFace, depuis la racine :

```bash
ml-image/.venv/bin/python ml-image/smoke_test.py \
  --trailer ml-image/tmp/staging-sample/trailer-short.mp4 \
  --poster ml-image/tmp/staging-sample/poster.jpg
```

Le test du 10 octobre 2026 a terminé avec trois lignes de personnages pour la vidéo et sept lignes de détections pour l’affiche, ainsi que les deux fichiers pickle attendus. Il valide l’exécution de bout en bout sur cet extrait uniquement ; les classifications et les correspondances de visages n’ont pas été évaluées.

Le fichier `trailer-short.mp4` est un extrait de dix secondes à partir de la trentième seconde. Ce fixture local n’est pas distribué avec le dépôt. Les identifiants des sorties du lanceur restent synthétiques.

## Entrée CSV de la pipeline

La CLI actuelle accepte `--source fichier.csv --mode infer` ou `--mode eval`. Elle n’accepte pas directement une URL Allociné en argument positionnel. Les colonnes nécessaires à l’inférence et à l’export sont :

`visa_number,allocine_id,allocine_url,trailer_url,poster_url`

`trailer_url` et `poster_url` doivent désigner les médias téléchargeables. Le lanceur local fournit des copies en cache et évite ces téléchargements. `--mode eval` collecte des résultats intermédiaires ; le calcul final des scores n’est pas raccordé.

Les variables `TEMP_FOLDER` et `OUTPUTS_FOLDER` choisissent les répertoires racines. `PREDICTIONS_FOLDER`, `DOWNLOADED_MEDIA_FOLDER`, `FINAL_PREDICTIONS_FOLDER`, `INTERMEDIATE_FOLDER` et `VISUALS_FOLDER` choisissent leurs sous-répertoires. Le lanceur les isole automatiquement.

## Limites et dépannage

- MediaPipe 0.10.21 contient une bibliothèque universelle ARM64/x86_64, mais ses métadonnées de wheel annoncent x86_64. `uv pip check` et `pip check` signalent donc la plateforme ; le traitement natif d’une image a été vérifié sur ce Mac ARM64.
- MediaPipe requiert un contexte graphique macOS, même dans ce profil CPU. Le sandbox peut en empêcher la création ; le test natif a été exécuté hors sandbox.
- Une vidéo vide ou des détections vides peuvent encore faire échouer la pipeline.
- L’export de la catégorie d’âge `70+` reste à corriger ; l’export actuel attend une plage avec tiret.
- Le rapprochement affiche/personnage ne dispose pas de seuil maximal de distance.
- Le test local ne valide pas Docker ni les dépendances historiques.
- En cas d’échec, consulter les logs et le répertoire `tmp/smoke-*` annoncé. Ne pas importer les sorties synthétiques dans une base réelle.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-07 | Joel Teixeira | Initial implementation |
| 2 | 2026-10-10 | Joel Teixeira | Reprise du travail sur le module. Réunification de toutes les branches isolés lié au travail ML. Profil CPU isolé, test d’export et procédure de test sur un film local ; clarification des limites de la pipeline récupérée ; exécution complète validée sur un extrait staging après ajout local du poids FairFace. |
