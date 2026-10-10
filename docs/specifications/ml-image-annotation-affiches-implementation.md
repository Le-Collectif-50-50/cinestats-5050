# Outil de correction des prédictions sur affiches

**Owner:** Data Team DataForGood
**Dernière révision:** 2026-10-10
**Status:** actif

## Objectif et périmètre

Créer une petite interface permettant de transformer les prédictions ML d’une affiche en annotations humaines validées. L’utilisateur voit les visages détectés, leur genre prédit et leur tranche d’âge estimée, puis valide, corrige, supprime ou ajoute des annotations.

Cette première version concerne les **affiches uniquement**, en usage local individuel. La vidéo, le travail simultané, l’identification nominative et l’ethnie sont hors périmètre. Aucune correction n’est publiée dans les tables applicatives `ric_*`.

Cette spécification définit le périmètre de la V1. L’implémentation autonome et ses commandes sont décrites dans le [guide annotation-poster](../../ml-image/annotation-poster/README.md).

## Parcours utilisateur

1. Renseigner un identifiant Allociné : rechercher le film et son affiche dans la base configurée, en lecture seule, puis importer une copie locale de l’image. Une affiche déjà préparée reste accessible sans connexion à la base. Afficher son titre, son état de relecture et la version du modèle.
2. Explorer l’image avec zoom et déplacement. Chaque boîte porte un identifiant et les étiquettes de genre et de tranche d’âge.
3. Sélectionner une boîte ou sa ligne dans le panneau latéral.
4. **Valider** la proposition, **corriger** sa position, sa taille, son genre ou sa tranche d’âge, ou **supprimer** une fausse détection.
5. **Ajouter** un visage oublié en dessinant sa boîte et en renseignant son genre perçu et sa tranche d’âge apparente.
6. Vérifier toute l’affiche, y compris les zones sans prédiction, puis la marquer comme validée.
7. Exporter la référence validée et le bilan des corrections.

L’image reste centrale ; le panneau latéral contient les annotations et leurs actions. Prévoir annuler/rétablir, un indicateur de sauvegarde et un bouton pour masquer les prédictions originales. Les états doivent être lisibles sans dépendre uniquement des couleurs.

## Règles d’annotation

- Une annotation représente **une apparition de visage**, même si le même personnage apparaît plusieurs fois sur l’affiche.
- La boîte encadre le visage visible, pas le corps. Les visages dessinés ou partiels peuvent être annotés ; un cas ambigu reçoit une note explicative.
- Catégories de genre proposées : « féminin perçu », « masculin perçu », « indéterminable ». Elles décrivent l’apparence annotée, pas l’identité de genre réelle.
- Tranches d’âge : `0-2`, `3-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+`, plus « indéterminable ». Elles reprennent les classes FairFace actuelles et décrivent l’âge apparent, pas un âge civil vérifié.
- Distinguer « non relu » de « indéterminable » : le premier est un état de travail, le second une décision humaine.
- Enregistrer une décision distincte pour la boîte, le genre et l’âge. Corriger le genre ne valide pas implicitement l’âge. Une action « Tout valider » peut approuver explicitement les trois champs.
- La validation globale exige une décision sur la boîte, le genre et l’âge de chaque visage conservé, ainsi qu’une confirmation de relecture complète. Une affiche sans visage peut être validée avec une liste vide.
- Toute modification après validation remet l’affiche en brouillon et invalide l’export courant comme référence approuvée.

## Architecture proposée

Regrouper l’outil dans **`ml-image/annotation-poster/`**, avec sa propre interface **Next.js/React**, son API **FastAPI**, ses dépendances, ses tests et son Compose. Les dossiers `frontend/` et `backend/` restent réservés au site Cinestats. Superposer les boîtes avec un SVG utilisant les dimensions originales de l’image : le zoom ne modifie pas les coordonnées enregistrées.

L’interface indépendante est accessible à la racine de son serveur local, sur le port 3010 par défaut. Les routes sont activées explicitement dans le Compose de cet outil, lié à l’interface locale. Une utilisation partagée nécessitera ensuite authentification et gestion des accès.

Le stockage initial repose sur des fichiers JSON dans un répertoire local ignoré par Git. Aucune migration PostgreSQL n’est nécessaire. L’API expose seulement une liste d’affiches, leur image, leurs prédictions, leur relecture et leur export. Elle utilise des identifiants internes, jamais des chemins arbitraires fournis par le navigateur.

La recherche Allociné utilise `ric_films.allocine_id`, puis `ric_posters.film_id`. La colonne historique `image_base64` peut contenir une URL : vérifier son format avant téléchargement. Les credentials restent côté serveur. Signaler film absent, correspondance ambiguë, affiche absente et base indisponible. Une réouverture ne remplace jamais une image ou une relecture existante. Sans prédictions préparées, afficher explicitement leur absence et permettre l’annotation manuelle.

L’inférence reste une préparation séparée : ouvrir ou modifier une affiche ne relance pas les modèles.

**Exigence de reproductibilité :** l’outil doit pouvoir être installé et exécuté localement via Docker, avec des dépendances figées et une procédure documentée. Les prérequis, la configuration et les données nécessaires doivent être explicités pour reproduire le même environnement sur une autre machine.

## Préparer les prédictions

Les CSV agrégés actuels ne suffisent pas : ils ne contiennent plus les boîtes. Ajouter un export JSON depuis les résultats ML en mémoire, avant leur agrégation tabulaire. Les pickle historiques locaux pourront être convertis par un script dédié ; l’interface n’acceptera pas de pickle téléversé.

**Particularité actuelle :** le genre et la tranche d’âge d’un visage d’affiche proviennent du personnage associé dans la bande-annonce. Ce n’est pas une classification indépendante de l’affiche. L’outil doit conserver cette provenance et permettre sa correction. Lancer une nouvelle analyse nécessite donc actuellement les deux médias.

La V1 exporte les résultats en mémoire avant agrégation CSV, après filtrage et association ; l’interface signale donc explicitement que les prédictions sont déjà filtrées. La conservation des détections rejetées avec leur motif reste une amélioration ultérieure. Une affiche sans prédictions reste annotable intégralement.

## Séparer prédictions et référence

| Fichier par affiche | Contenu |
| --- | --- |
| `manifest.json` | Version du format, film, dimensions, empreinte de l’image, identifiant d’exécution, code, poids et paramètres |
| `predictions.json` | Prédictions originales immuables : identifiant, boîte, genre, `age_range`, provenance et scores réellement disponibles |
| `review.json` | Révision, état brouillon/validé, annotateur, dates, décisions par champ, ajouts et corrections du genre, de l’âge et des boîtes |
| `reference.json` | Export des boîtes, genres et tranches d’âge validés, relié à la révision de relecture |

Les boîtes utilisent `[x1, y1, x2, y2]` en pixels de l’image originale, avec une surface positive et des coordonnées dans l’image. Chaque annotation possède un identifiant stable ; les ajouts humains n’ont pas d’identifiant de prédiction source.

Stocker la tranche dans `age_range` sous forme de classe textuelle ; `unknown` représente « indéterminable ». Un champ absent reste non renseigné et ne vaut pas décision humaine. Conserver `70+` comme classe ouverte, sans borne supérieure inventée ; ne pas convertir `unknown` en âge zéro. L’export CSV historique ne gère pas correctement `70+` : le nouvel export JSON doit couvrir ce cas.

Ne pas confondre confiance de détection, confiance du genre et confiance de l’âge. Un score absent reste absent. Une suppression reste traçable dans la relecture, mais n’apparaît pas dans la référence finale.

Sauvegarder automatiquement les décisions, avec écriture atomique. Afficher les erreurs de sauvegarde. Contrôler le numéro de révision pour éviter qu’un deuxième onglet écrase des modifications récentes. Refuser une relecture associée à une image d’empreinte différente.

## Évaluation et limites

La V1 fournit une référence exportable et des comptes de propositions validées, corrigées, supprimées ou ajoutées. Ces comptes ne constituent pas, seuls, une mesure d’exactitude.

Les scores de détection, de genre et de tranche d’âge seront calculés ensuite, par comparaison entre prédictions originales et référence validée. Pour l’âge, mesurer les erreurs par tranche, les confusions entre tranches et le taux d’indétermination. Réserver les films de validation aux comparaisons finales, sans les utiliser pour ajuster les seuils.

L’assistance du modèle peut influencer la relecture. Pour contrôler ce biais, prévoir ensuite un sous-ensemble annoté sans préannotations ou une seconde relecture indépendante. L’ajout des visages manqués est indispensable dès la V1.

## Étapes et critères d’acceptation

1. **Contrat et export** : préparer une affiche issue de staging, sans écriture en base ; vérifier la provenance et les coordonnées.
2. **Éditeur** : affichage, zoom, sélection, validation et correction des boîtes, du genre et de l’âge, suppression et ajout.
3. **Persistance** : reprise après fermeture, annuler/rétablir, erreurs visibles et protection contre les écrasements.
4. **Validation** : export de référence et tests sur affiche normale, sans prédictions, sans visage et avec fausses détections ; couvrir aussi `70+`, un âge absent et un âge indéterminable.

La V1 sera acceptée si les prédictions originales restent intactes, les boîtes restent alignées après zoom, toutes les actions sont sauvegardées et une référence ne peut être exportée comme validée avec des boîtes ou attributs non relus. Le genre et l’âge doivent pouvoir être corrigés indépendamment, sans altérer les valeurs originales. Une modification ultérieure doit invalider cette validation.

Vérifications prévues : tests API de sauvegarde et de validation, test navigateur du parcours complet, contrôle TypeScript et build frontend. La qualité des prédictions n’est pas un critère de réussite de l’éditeur.

## Références

- [Cadrage du jeu d’évaluation](ml-image-evaluation-validation.md)
- [Architecture actuelle du module](../architecture/ml-image-architecture-description-pipeline-phase-1.md)
- [Installation et test local](../../ml-image/README.md)

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-10 | Joel Teixeira | V1 de correction des affiches : genre, tranche d’âge, recherche Allociné en lecture seule, Docker reproductible et outil autonome sous ml-image/annotation-poster. |
