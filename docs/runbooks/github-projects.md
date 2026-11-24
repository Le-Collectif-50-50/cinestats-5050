# Organiser les chantiers dans GitHub Projects

**Owner:** Joel Teixeira
**Dernière révision:** 2026-11-24
**Status:** actif

## Retrouver le suivi

Les deux Projects publics appartiennent à `Le-Collectif-50-50` et sont liés aux dépôts `cinestats-5050` et `cinestats-infra`.

| Project | Périmètre | Label de routage |
| --- | --- | --- |
| [Nouveau module ingestion](https://github.com/orgs/Le-Collectif-50-50/projects/1) | Airbyte, dbt, scraping, orchestration, qualification des données et opérations Metabase associées | `projet: ingestion` |
| [Migration vers l’infrastructure Collectif 50/50](https://github.com/orgs/Le-Collectif-50-50/projects/2) | Migration, déploiement, accès, sécurité, supervision et reprise | `projet: infrastructure` |

Ajouter le label correspondant à une issue ou PR pour la faire entrer dans le Project. Les deux labels permettent un suivi dans les deux chantiers. Le retrait du label conserve la participation historique ; un retrait du Project doit être explicite. Les issues et PR gardent leur dépôt, leur numéro, leur état et leurs discussions.

Les vues **Pilotage**, **À valider et blocages**, **PR à relire**, **Livraisons** et **Historique** séparent le travail ouvert, les validations, les revues et les clôtures. Les éléments historiques restent visibles et ne sont pas archivés automatiquement. Le [wiki](https://github.com/Le-Collectif-50-50/cinestats-5050/wiki) sert uniquement de navigation ; les guides techniques restent versionnés dans les dépôts.

## Comprendre les statuts

Le workflow `Project sync` lit les labels des issues, sans les modifier. Le [workflow des statuts d’issues](github-statuts-issues.md) reste responsable des transitions liées aux PR. Les modifications manuelles du champ Project **Status** sont remplacées à la réconciliation suivante.

| État actuel de l’élément | Status du Project |
| --- | --- |
| Issue fermée avec raison `COMPLETED` | Terminé |
| Issue fermée pour une autre raison ou sans raison disponible | Abandonné |
| Issue ouverte avec `statut: bloqué` | Bloqué, prioritaire sur les autres labels |
| Issue ouverte avec `statut: en cours` | En cours |
| Issue ouverte avec `statut: à valider` | À valider |
| Autre issue ouverte | À faire |
| PR fusionnée | Terminé |
| PR fermée sans fusion | Abandonné |
| PR ouverte, y compris brouillon | En cours |

La fusion ne prouve ni le déploiement ni la validation métier. Une issue encore ouverte conserve son statut issu des labels, même lorsque sa PR est fusionnée.

Les milestones décrivent des livrables, sans échéance imposée : collecte/orchestration, publication dbt, qualification, migration/déploiement, accès/sécurité et supervision/reprise. Ils sont propres aux dépôts. Un élément partagé entre Projects conserve un seul milestone, choisi selon son livrable technique principal. La clôture d’un milestone reste manuelle après vérification du livrable ; l’import historique ne certifie pas une migration en production.

## Installer l’authentification dédiée

La planification nécessite une GitHub App dédiée ; `GITHUB_TOKEN` ne reçoit aucun droit d’écriture supplémentaire. L’App existante de publication du lineage dbt n’est pas réutilisée.

1. Dans [les paramètres des GitHub Apps de l’organisation](https://github.com/organizations/Le-Collectif-50-50/settings/apps), créer **CineStats Projects Sync**. Homepage : `https://github.com/Le-Collectif-50-50/cinestats-5050`. Désactiver le webhook et limiter l’installation à cette organisation.
2. Accorder uniquement **Organization permissions → Projects: Read and write**, **Repository permissions → Issues: Read-only**, **Pull requests: Read-only** et **Metadata: Read-only** (implicite). Ne pas activer les anciens Projects de dépôt.
3. Installer l’App sur les seuls dépôts `cinestats-5050` et `cinestats-infra`.
4. Générer une clé privée et définir les secrets Actions **PROJECTS_APP_ID** et **PROJECTS_APP_PRIVATE_KEY** dans `cinestats-5050`. Le premier contient l’App ID ; le second contient le PEM complet. Ne jamais versionner cette clé.
5. Après intégration du workflow dans `main`, lancer **Actions → Project sync → Run workflow**, avec **dry_run** activé. Contrôler le journal puis relancer sans simulation.

L’App peut modifier les Projects de l’organisation : son installation exige une validation de l’administrateur. Les tokens d’installation sont temporaires et révoqués par l’action de génération de token. Le workflow demande explicitement les seules permissions nécessaires.

Le workflow demande une exécution toutes les quinze minutes ; GitHub peut retarder les déclenchements planifiés. Sans secrets, il échoue avec un message indiquant les noms à configurer. Une erreur de permission, un Project absent ou un champ Status incomplet fait également échouer le run, sans annoncer une synchronisation réussie. Corriger la cause puis relancer ; les ajouts et mises à jour déjà effectués ne sont pas dupliqués.

## Vérifier et relancer

Prérequis local : Node.js 20 ou supérieur et GitHub CLI authentifié comme `ndretex`, avec le scope `project`. Les commandes ci-dessous ne nécessitent pas la clé privée de l’App.

```bash
node --test .github/scripts/issue-status.test.cjs .github/scripts/project-sync.test.cjs
node .github/scripts/project-sync.cjs --dry-run
node .github/scripts/project-sync.cjs --apply
```

La simulation est le comportement par défaut. La configuration des dépôts, titres et labels se trouve dans [`.github/projects.json`](../../.github/projects.json). La synchronisation lit l’état courant, traite les deux dépôts et pagine les issues, PR, Projects et éléments de Project. Elle ignore les brouillons de Project et les contenus inaccessibles, sans les supprimer. Elle échoue en présence de Projects homonymes ou de doublons de contenu.

L’amorçage historique est reproductible, mais doit rester une opération administrateur ponctuelle :

```bash
node .github/scripts/project-setup.cjs --dry-run
node .github/scripts/project-setup.cjs --apply
```

Ce script réutilise les Projects portant les titres attendus ou les deux Projects vides initialement sans titre. Il configure leur visibilité publique, les liens aux dépôts, les statuts et les vues. Il crée les labels et milestones manquants, ajoute les labels aux éléments explicitement référencés dans `SEEDS` et attribue les milestones uniquement lorsqu’ils sont absents. Il ne modifie ni les états, ni les discussions, ni les responsables, ni les liens de résolution. Les tableaux `SEEDS` sont la source de l’import initial, pas un export de résultats. Pour les nouveaux éléments, utiliser les labels de routage.

Après configuration, contrôler les regroupements des vues dans l’interface GitHub : le board **Pilotage** par Status et la vue **Livraisons** par milestone, avec les dépôts identifiables. L’API publique de configuration des vues expose les champs visibles et les filtres, mais pas ces regroupements.

Références : [automatiser Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project), [générer un token d’App](https://github.com/actions/create-github-app-token), [milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones).

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-24 | Joel Teixeira | Deux chantiers transverses, historique, routage, statuts et installation de l’App dédiée. |
