# Pipeline ML image : architecture implémentée et limites

**Owner:** Julien Commes
**Dernière révision:** 2026-10-10
**Status:** actif

## Périmètre et niveau de validation

Le module `ml-image` réalise une inférence sur des bandes-annonces et des affiches. Il détecte les visages, estime des attributs, regroupe les détections vidéo et associe les visages d’affiche aux groupes vidéo. Il exporte des fichiers locaux ; il n’insère pas ses résultats en base et ne constitue pas un service API ou un job Prefect.

Ce document décrit le code présent, y compris ses limitations. Pour installer les dépendances et exécuter les tests, suivre le [README ML](../../ml-image/README.md).

| Fonctionnalité | État constaté |
| --- | --- |
| Détection, classification, embeddings et regroupement vidéo | Implémentés ; parcours CPU exécuté sur un extrait |
| Rapprochement affiche/vidéo | Implémenté ; absence de seuil de rejet |
| Vote pondéré et indicateurs de présence | Implémentés ; formules précisées ci-dessous |
| Traitement CSV, pickle et exports CSV | Implémentés ; test d’export et test sur un film réussis |
| Collecte de résultats pour évaluation | Code présent ; mode `eval` non validé de bout en bout |
| Annotation manuelle et calcul de scores | Fonctions présentes ; intégration incomplète et appels obsolètes |
| Vidéo annotée | Branche optionnelle présente, non validée |
| Affiche annotée depuis la CLI | Désactivée dans l’appel de `predict_one_item` |
| CUDA | Sélection automatique présente ; exécution non validée |
| Apple MPS | Non implémenté |
| Nettoyage/profilage explicite de mémoire CUDA | Non implémenté |
| Validation du schéma CSV et reprise fiable des erreurs | Non implémentées |

Le 10 octobre 2026, le test CPU sur macOS ARM64 a produit deux pickle, trois lignes de personnages vidéo et sept lignes de détections affiche pour un extrait de dix secondes / 240 images de **Natacha, hôtesse de l’air**. Le test confirme le fonctionnement de ce parcours, pas la qualité des classifications, des regroupements ou des correspondances. L’échantillon et les poids sont locaux et non versionnés.

## Organisation du code

| Fichier | Responsabilité |
| --- | --- |
| [main.py](../../ml-image/main.py) | Arguments CLI, répertoires et appel du gestionnaire |
| [pipelines.py](../../ml-image/scripts/pipelines.py) | Modes `infer`/`eval`, traitement d’un film et orchestration vidéo/affiche |
| [vision_detection.py](../../ml-image/scripts/vision_detection.py) | YOLO, redimensionnement et extraction des visages |
| [vision_classifiers.py](../../ml-image/scripts/vision_classifiers.py) | FairFace et seuils d’attribution des classes |
| [filter_detections.py](../../ml-image/scripts/filter_detections.py) | Filtres de sélection, pondération et pose MediaPipe |
| [faces_clustering.py](../../ml-image/scripts/faces_clustering.py) | FaceNet, Chinese Whispers, vote et rapprochement affiche |
| [utils.py](../../ml-image/scripts/utils.py) | Médias, extraction des images, calculs de surface et exports |
| [evaluation_annotation.py](../../ml-image/scripts/evaluation_annotation.py) | Annotation, scores et enregistrement des résultats intermédiaires |
| [smoke_test.py](../../ml-image/smoke_test.py) | Test CPU sur des copies isolées de deux médias locaux |

`model_architectures.py` contient d’autres architectures, non utilisées par le parcours d’inférence actuel.

## Entrées et orchestration

Depuis `ml-image/`, avec les dépendances et poids disponibles :

```bash
.venv/bin/python main.py --source /chemin/films.csv --mode infer --istart 0 --istop 1
```

`handler()` accepte uniquement un nom se terminant par `.csv` et les modes `infer` ou `eval`. `istart:istop` est une tranche de lignes, borne de fin exclue. L’aide CLI mentionne d’autres sources, mais le gestionnaire ne les accepte pas.

| Colonne | Utilisation |
| --- | --- |
| `visa_number` | Noms des médias en cache et rapprochement lors de l’export |
| `allocine_id` | Identifiant exporté dans les CSV |
| `allocine_url` | Métadonnée lue par le chargeur |
| `trailer_url` | URL directe de la vidéo à télécharger |
| `poster_url` | URL directe de l’affiche à télécharger |

`--column_identifier` vaut `visa_number`. Le téléchargement et l’export continuent toutefois à supposer `visa_number` ; changer cet argument ne rend pas le parcours indépendant de cette colonne. Aucun validateur préalable ne contrôle les colonnes, leurs types ou les URL.

`load_data_from_links()` réutilise les fichiers `{visa_number}.mp4` et `{visa_number}.jpg` déjà présents, sinon les télécharge. Il attend les deux médias ; l’affiche facultative décrite dans certains arguments n’est pas gérée par ce chargeur. Les téléchargements n’imposent ni délai maximal ni contrôle du statut HTTP.

`predict_one_item()` choisit CUDA si `torch.cuda.is_available()`, sinon CPU. Il appelle successivement `infer_on_trailer()` puis `infer_on_poster()`. Le lanceur de test masque CUDA pour imposer le CPU. MediaPipe peut malgré cela nécessiter un contexte graphique macOS ; ce n’est pas une sélection MPS pour PyTorch.

## Analyse de la bande-annonce

1. **Lecture complète.** `frame_capture()` charge toutes les images BGR dans un tableau NumPy et lit les FPS OpenCV. Il n’y a ni sous-échantillonnage ni lecture progressive dans la pipeline.
2. **Surface de référence.** `compute_params()` utilise `largeur × (largeur / 2.478)`. La fonction de détection des bandes noires existe, mais n’est pas appelée ici. Aucun rejet spatial des visages situés hors de cette surface théorique n’est effectué. La netteté globale est calculée sans ajustement actif des seuils.
3. **Détection.** YOLO Face reçoit des images RGB redimensionnées à 640 × 640, par lots. Les boîtes sont remises à l’échelle d’origine. Le détecteur initialise aussi YOLO personne, même pour une demande de visages. Aucun agrandissement configurable des boîtes n’est implémenté.
4. **Sélection initiale.** `filter_detections_clustering()` conserve les visages satisfaisant le filtre de surface relative et celui de confiance YOLO.
5. **Classification.** FairFace/ResNet34 produit des classes et probabilités. Une classe devient `unknown` sous son seuil propre. Les seuils sont des valeurs par défaut de `classify_faces()`, non des options CLI : genre ≈ 0,965932 ; âge ≈ 0,595667 ; ethnie ≈ 0,810392.
6. **Pondération.** `filter_detections_classifications()` conserve les détections et leur attribue `classification_weight`, nombre de critères satisfaits parmi confiance, netteté et pose, donc de 0 à 3. Malgré le nom `min_conf_cla`, le critère de confiance lit `det['conf']` — la confiance YOLO — et non une probabilité FairFace. La pose utilise la coordonnée z du nez de MediaPipe ; ce n’est pas un z-score statistique. Le critère d’ouverture de bouche n’est pas actif.
7. **Embeddings et groupes.** FaceNet/InceptionResnetV1, poids VGGFace2, encode les visages en 160 × 160. Chinese Whispers regroupe les vecteurs avec un seuil de 0,92 par défaut. Un groupe est conservé s’il représente au moins 3 % des détections regroupées. Ce minimum est défini dans la fonction, pas exposé dans la CLI.
8. **Agrégation.** La méthode appelée `majority` additionne les poids par classe et choisit la classe de poids maximal. Il s’agit d’un vote pondéré, pas d’une moyenne de probabilités. `unknown` est retiré du vote dès qu’une autre classe existe. Les égalités, notamment entre poids nuls, n’ont pas de règle de fiabilité supplémentaire.

Les crops transmis à FairFace et FaceNet restent BGR : contrairement au détecteur et à MediaPipe, leurs transformations n’effectuent pas explicitement la conversion RGB. Ce point doit être vérifié avant de conclure sur la qualité des prédictions.

### Indicateurs vidéo

Pour un groupe de `N` détections, la durée exportée vaut `N / fps`. Elle compte les détections, pas les images distinctes. Elle ne mesure pas une durée continue et peut surcompter si plusieurs détections d’une même image sont regroupées.

La surface exportée est `somme(surfaces des boîtes) / (surface de référence × N)`. C’est une fraction moyenne sur les détections du groupe, pas un pourcentage multiplié par 100 ni une moyenne sur toutes les images de la vidéo. `frames_bboxes` ne conserve qu’une boîte par indice d’image si plusieurs détections du groupe partagent cet indice.

`infer_on_trailer()` retourne réellement trois objets : les groupes agrégés, les embeddings et leurs `perso_id`. Certaines annotations de retour du code sont obsolètes.

## Analyse de l’affiche

La détection utilise YOLO Face et la surface réelle `hauteur × largeur`. Le filtre affiche applique uniquement la confiance YOLO ; `min_area` est transmis, mais aucun filtre de surface n’est activé.

Les embeddings d’affiche sont comparés aux embeddings des détections vidéo appartenant aux groupes conservés. Pour chaque visage, `assign_poster()` choisit la détection vidéo la plus proche en distance euclidienne et lui emprunte les attributs de son groupe. Il n’y a pas de classification FairFace indépendante de l’affiche dans ce parcours.

Il n’existe aucun seuil maximal de distance ni contrainte d’association unique. Plusieurs visages d’affiche peuvent recevoir le même groupe. Un visage n’est supprimé comme non associé que lorsqu’aucun candidat n’a pu être choisi ; un candidat éloigné n’est pas rejeté pour cette raison.

`occupied_area` vaut la surface de la boîte divisée par celle de l’affiche. `infer_on_poster()` retourne une liste de détections enrichies.

## Sorties et stockage

Les chemins par défaut sont construits par `main.py` :

| Chemin | Contenu |
| --- | --- |
| `tmp/downloaded_media/` | Copies locales des vidéos et affiches |
| `tmp/stored_predictions/{identifiant}_trailer_predictions.pkl` | Liste des groupes vidéo |
| `tmp/stored_predictions/{identifiant}_poster_predictions.pkl` | Liste des détections affiche associées |
| `outputs/final_predictions/predictions_on_trailers.csv` | Agrégation tabulaire vidéo |
| `outputs/final_predictions/predictions_on_posters.csv` | Agrégation tabulaire affiche |
| `outputs/intermediate_results/` | Enregistrements du mode `eval` |

Les variables de répertoire sont décrites dans le [README](../../ml-image/README.md#entrée-csv-de-la-pipeline). `infer_pipeline()` sauvegarde les deux pickle avant de supprimer les copies des médias. Ce nettoyage n’est pas garanti en cas d’exception. Le lanceur local utilise un dossier unique par test pour éviter de mélanger les résultats.

`gather_and_save_predictions()` parcourt les fichiers dont le nom contient `poster` ou `trailer` dans le répertoire de prédictions. Il ne limite pas explicitement cette collecte aux fichiers de l’exécution courante : réutiliser un dossier peut mélanger d’anciens résultats ou provoquer un échec de rapprochement avec le CSV source.

### Schéma pickle vidéo

Chaque groupe contient les clés suivantes, avec leur orthographe actuelle :

| Clé | Contenu |
| --- | --- |
| `age`, `gender`, `ethnicity` | Classes agrégées, éventuellement `unknown` |
| `occurence` | Nombre de détections divisé par les FPS |
| `area occupied` | Fraction de surface moyenne décrite ci-dessus |
| `label` | Identifiant local du groupe conservé |
| `frames_bboxes` | Dictionnaire indice d’image → boîte `[x1, y1, x2, y2]` |
| `perso_ids` | Identifiants des détections appartenant au groupe |

### Schéma pickle affiche

Chaque détection conserve `bbox`, `conf`, `cropped_face` (tableau NumPy BGR), `frame_id`, `perso_id`, `movie_id` et `poster_weight`. Le rapprochement ajoute `gender`, `age`, `ethnicity`, `label` et `occupied_area`. Les boîtes sont des coordonnées de coins, pas `[x, y, largeur, hauteur]`.

### Schémas CSV

Colonnes communes : `visa_number,allocine_id,gender,age_min,age_max,ethnicity`.

- Affiche : colonne supplémentaire `poster_percentage`, fraction de surface malgré son nom.
- Vidéo : colonnes supplémentaires `time_on_screen` en secondes et `average_size_on_screen` en fraction.

Les identifiants de groupes et les confiances ne sont pas exportés dans ces CSV. `unknown` pour l’âge est converti en bornes `0,0`. L’âge `70+` provoque un échec dans le découpage actuel, qui suppose une chaîne contenant `-`.

## Évaluation et visualisations

`evaluate_pipeline()` appelle la prédiction en mode `eval`. Les fonctions d’enregistrement écrivent `intermediate_results_trailer.csv` et `intermediate_results_poster.csv` ; les attributs agrégés vidéo sont ensuite reportés dans le premier fichier. Ce mode n’appelle pas les exports finaux du mode `infer` et n’effectue pas le même nettoyage des médias.

L’appel final au calcul des scores est commenté. Les helpers d’annotation ne forment pas un parcours validé : par exemple, `get_faces()` appelle `crop_areas_of_interest()` sans son argument requis `movie_id`. `compute_params()` attend le mode `evaluate` pour un export de paramètres, alors que la CLI transmet `eval`.

`--store_visuals` déclenche la branche d’annotation vidéo, qui écrit dans `example/{movie_id}.avi`. Elle n’utilise pas le dossier `outputs/stored_visuals` créé par `main.py` et ne garantit pas la création de `example/`. L’appel affiche force `store_visuals=False` dans `predict_one_item()`. Les fonctions de dessin existent, mais ce parcours n’a pas été testé.

## Paramètres réellement raccordés

| Paramètre | Effet actuel |
| --- | --- |
| `--source`, `--mode`, `--istart`, `--istop` | CSV, mode et sélection de lignes |
| `--batch_size` | Taille des lots de détection/classification/embedding ; défaut 64 |
| `--num_cpu` | Nombre de threads donné au détecteur ; défaut 8. Le classifieur le remet à 1 par défaut : ce réglage n’est pas globalement stable |
| `--min_area`, `--max_area` | Surface relative vidéo ; défauts ≈ 0,076229 et 1,0 |
| `--min_conf` | Confiance de détection vidéo/affiche ; défaut 0,0 |
| `--min_conf_cla` | Confiance YOLO dans la pondération ; défaut ≈ 0,805975 |
| `--min_sharpness_cla`, `--max_z_cla` | Netteté et pose dans la pondération ; défauts ≈ 144,397649 et −0,181548 |
| `--cluster_model`, `--cluster_threshold` | Seul `chinese_whispers` est implémenté ; seuil par défaut 0,92 |
| `--agr_method` | Seul `majority`, vote pondéré, est implémenté |
| `--store_visuals` | Vidéo seulement dans l’orchestration actuelle ; désactivé par défaut |
| `--source_image`, `--min_sharpness`, `--max_z`, `--min_mouth_opening` | Déclarés dans la CLI, non utilisés par le gestionnaire |
| `--min_mouth_opening_cla` | Transmis mais aucun filtre actif ne l’utilise |

Il n’y a pas d’option CLI `--device` ni `--bbox_expand_factor`.

## Fiabilité et travail restant

Les points suivants sont des limites du code, pas des fonctionnalités disponibles :

- Les vidéos vides, FPS nuls ou listes de détections vides ne sont pas traités systématiquement. Des accès `[0]` figurent même dans des chaînes de logs de niveau debug.
- Les exceptions par film sont journalisées puis ignorées. Le message « All films … analyzed » peut donc apparaître malgré des films en échec. Il n’existe pas de bilan fiable des réussites et échecs ; le lanceur de test contrôle les fichiers produits.
- Les images, détections et embeddings restent en mémoire. Les lots limitent certains calculs, mais pas le chargement initial. Aucun profilage GPU, `empty_cache()` ou nettoyage explicite par film n’est implémenté.
- Les modèles sont recréés lors des appels de traitement ; leur réutilisation entre films n’est pas organisée.
- Docker utilise les dépendances historiques, une installation CUDA 11.8 et le téléchargement des poids à la construction. Son `ENTRYPOINT` est commenté. Il n’a pas été validé par le test CPU local.
- La validation qualitative nécessite des annotations de référence, des mesures d’erreur et une revue des conversions de couleurs, des seuils, des votes et des correspondances.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-07 | Joel Teixeira | Initial implementation |
| 2 | 2026-10-10 | Joel Teixeira | Audit du code récupéré et du test CPU ; description en français des entrées, calculs, sorties, paramètres actifs et fonctionnalités incomplètes. |
