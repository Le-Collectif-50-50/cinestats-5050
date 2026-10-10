# ML-image : intégration et jeu d’évaluation

**Owner:**
**Dernière révision:** 2026-10-10
**Status:** brouillon

## Objectif

Analyser les affiches et bandes-annonces pour détecter les visages, reconnaître un même personnage entre images et estimer son genre et sa tranche d’âge apparente. L’objectif métier est de mesurer la présence et le temps à l’écran par genre.

La reconnaissance désigne ici le regroupement des apparitions d’un personnage, sans identification nominative. Le modèle estime un genre à partir de l’apparence ; prévoir une catégorie « indéterminé ». Le pipeline actuel mesure principalement la visibilité des visages, pas toute présence corporelle à l’écran.

## État actuel

| Élément | Statut |
| --- | --- |
| Pipeline vidéo et affiche | Fonctionnelle sur un extrait CPU de test ; exports CSV et pickle |
| Intégration ingestion / Prefect | Aucun déclenchement ML raccordé |
| Base et backend | Tables et imports CSV existants ; calcul d’indicateurs depuis les tables `ric_*` |
| Interface | Indicateurs transmis aux composants, mais statistiques masquées |
| Évaluation | Éditeur autonome d’affiches disponible ; scores ML encore partiels, aucun corpus validé figé |

Le passage ML → base reste manuel. La preview peut importer les CSV historiques, sans relancer l’inférence. Le test réalisé valide l’exécution, pas l’exactitude des résultats. Les prédictions en base ne portent pas de version du modèle ni de statut de validation.

## Définir les indicateurs avant l’évaluation

Deux durées répondent à des questions différentes :

- **Secondes-personnages** : addition des présences individuelles. Deux personnages présents cinq secondes donnent dix secondes-personnages.
- **Durée de présence par genre** : temps avec au moins un personnage du genre considéré. Le même exemple donne cinq secondes.

Le calcul actuel se rapproche des secondes-personnages, à partir des détections. Recommandation : distinguer les deux mesures et préciser leurs dénominateurs. Les durées de plusieurs genres peuvent se chevaucher. Conserver les résultats indéterminés dans le bilan.

Pour les affiches, définir si l’indicateur cible est le nombre de personnages, la surface cumulée des visages ou leur surface moyenne. Le backend calcule actuellement une moyenne par personnage féminin, pas une surface totale.

## Construire un premier jeu de référence

1. **Sélectionner un corpus pilote**, par exemple dix films avec affiche et courts extraits variés : profils, petits visages, groupes, scènes sombres. Ce pilote ne suffit pas à démontrer une fiabilité générale.
2. **Corriger les préannotations du modèle** : valider, corriger ou supprimer les propositions, puis ajouter les visages manqués. Relire séparément la boîte, le genre et la tranche d’âge apparente, avec une réponse « indéterminable » si nécessaire. Conserver les prédictions originales séparément de la référence humaine. Commencer par les affiches ; les intervalles vidéo viendront ensuite. Prévoir un sous-ensemble annoté sans préannotations pour contrôler le biais d’assistance.
3. **Séparer les films** entre un ensemble de réglage et un ensemble de validation réservé. Aucun film partagé ; ne pas ajuster les seuils sur la validation.
4. **Faire relire un sous-ensemble** par une seconde personne et résoudre les désaccords avec des consignes communes.

## Mesurer les erreurs

| Étape | Mesures attendues |
| --- | --- |
| Détection | Visages manqués et fausses détections |
| Genre | Erreurs par catégorie et taux d’indétermination |
| Tranche d’âge | Erreurs par tranche, confusions entre tranches et taux d’indétermination |
| Regroupement | Personnages fusionnés ou fragmentés |
| Affiche / vidéo | Associations correctes et injustifiées |
| Indicateurs métier | Écart sur les durées et surfaces annotées |

Chaque exécution doit produire un rapport comparable : corpus, annotations, version du code, poids, paramètres, résultats et exemples d’erreurs.

## Suite recommandée

**Priorité 1 — Protocole.** Valider les indicateurs, catégories de genre, tranches d’âge et critères d’acceptation.

**Priorité 2 — Évaluation reproductible.** Préparer le corpus, réparer les outils d’annotation et raccorder les scores. Vérifier notamment la conversion BGR/RGB, la pondération et le seuil de rejet des correspondances.

**Priorité 3 — Intégration contrôlée.** Après évaluation, automatiser Prefect → ML → import. Versionner les exécutions, suivre les échecs et distinguer les résultats validés avant affichage public.

## Références

- [Spécification de l’outil d’annotation des affiches](ml-image-annotation-affiches-implementation.md)
- [Installation et test local](../../ml-image/README.md)
- [Architecture implémentée et limites](../architecture/ml-image-architecture-description-pipeline-phase-1.md)

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-10 | Joel Teixeira | Cadrage de l’intégration, des indicateurs par genre et du premier jeu d’évaluation ; approche par correction assistée, prise en compte des tranches d’âge et lien vers la spécification affiches. |
