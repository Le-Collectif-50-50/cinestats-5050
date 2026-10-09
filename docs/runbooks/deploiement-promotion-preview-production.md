# Valider en preview avant de promouvoir en production

**Owner:** Data Team DataForGood
**Last reviewed:** 2026-10-09
**Status:** active

## Historique du document

| # | Date | Author | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-09 | Joel Teixeira | Procédure de promotion, validation en preview et contrôle du commit avant production. |

## Objectif

Déployer les changements sur un environnement de test, vérifier les parcours utilisateurs, puis déployer la version validée en production.

Dans ce dépôt, **staging désigne l'environnement `preview`**. Le script n'accepte pas de cible nommée `staging`.

| Usage | Branche | Site |
| --- | --- | --- |
| Validation avant production | `preview` | <https://preview.cinestats5050.fr> |
| Application publique | `production` | <https://cinestats5050.fr> |

Le script [`scripts/promote.sh`](../../scripts/promote.sh) fait avancer la branche distante choisie jusqu'au commit courant de `origin/main`. Ce push déclenche le workflow [`Deploy`](../../.github/workflows/deploy.yml), qui construit les images, déploie l'application et effectue des contrôles HTTP.

**Les deux promotions partent de `main`.** La promotion en production ne copie pas automatiquement le commit de `preview` et ne vérifie pas sa validation.

## Prérequis

- Exécuter les commandes depuis la racine du dépôt, avec Bash et Git disponibles.
- Vérifier que `origin` pointe vers `Le-Collectif-50-50/cinestats-5050` et disposer du droit de pousser sur la branche cible.
- Installer et authentifier GitHub CLI (`gh`) pour utiliser `--watch` et les commandes de suivi ci-dessous.
- Avoir fusionné les changements à déployer dans le `main` distant. Les commits locaux non poussés et les fichiers non commités ne sont pas déployés.
- Disposer des environnements GitHub et serveurs configurés selon le [guide de déploiement](../DEPLOYMENT.md).

Vérifications locales :

```bash
git remote -v
gh auth status
```

## 1. Promouvoir en preview

Cette commande modifie la branche distante `preview` et déclenche son déploiement :

```bash
scripts/promote.sh preview --watch
```

Le script récupère les branches distantes, vérifie que la promotion conserve l'historique existant, puis pousse. Avec `--watch`, il cherche le workflow correspondant au commit pendant environ 30 secondes, puis attend sa fin. Un échec du workflow produit un code de sortie non nul.

Relever le **SHA complet** (identifiant du commit) du déploiement réussi :

```bash
gh run list --repo Le-Collectif-50-50/cinestats-5050 \
  --branch preview --workflow Deploy --limit 5 \
  --json databaseId,headSha,status,conclusion,url
```

Choisir l'exécution correspondant à la promotion, avec `status: completed` et `conclusion: success`. Conserver son URL et son `headSha` avec le résultat des vérifications. En cas de rollback manuel, consulter aussi le commit demandé au workflow : `headSha` seul ne décrit pas nécessairement la version redéployée.

## 2. Vérifier l'application

Ouvrir <https://preview.cinestats5050.fr> après la réussite du workflow.

- Vérifier le chargement de l'accueil et des pages principales.
- Vérifier l'affichage des graphiques et des données attendues.
- Tester les filtres et la navigation entre pages.
- Tester précisément les fonctionnalités modifiées par les changements déployés.
- Vérifier les erreurs visibles et les requêtes API en échec dans les outils du navigateur.

Les contrôles automatiques vérifient que le site et l'API répondent, ainsi que le contenu de `robots.txt`. Ils ne valident pas tous les parcours métier.

La preview dispose de sa propre base PostgreSQL et de réglages spécifiques. Ses données peuvent différer de la production. Metabase peut utiliser la même instance que la production ; voir les [particularités de la preview](../DEPLOYMENT.md#preview).

Si une régression apparaît, corriger via une PR vers `main`, puis recommencer la promotion et la validation en preview. Ne pas promouvoir cette version en production.

## 3. Vérifier le commit avant production

Remplacer la valeur ci-dessous par le SHA complet du déploiement preview validé, puis exécuter dans Bash :

```bash
VALIDATED_SHA='remplacer-par-le-sha-complet-valide'
git fetch origin main preview production
git rev-parse origin/main origin/preview origin/production
if [ "$(git rev-parse origin/main)" = "$VALIDATED_SHA" ]; then
  echo 'main correspond au commit validé.'
else
  echo 'STOP : main a changé. Refaire la validation en preview.'
fi
```

Si `main` a changé, ne pas poursuivre avec la commande de production. Promouvoir le nouveau `main` en preview et le tester d'abord.

**Ce contrôle ne verrouille pas `main`.** Le script effectue un nouveau fetch au lancement. Coordonner la promotion avec l'équipe pour éviter une fusion entre ce contrôle et la promotion. Le script ne propose pas d'argument permettant de figer un SHA.

Si la livraison comprend une migration de schéma, préparer son exécution selon le [guide production](../DEPLOYMENT.md#production). Les migrations sont automatiques en preview, mais pas en production ; `promote.sh` ne les exécute pas lui-même.

## 4. Promouvoir en production

Après validation fonctionnelle et contrôle du commit :

```bash
scripts/promote.sh production --watch
```

Cette commande modifie la branche distante `production` et déclenche son déploiement. Si GitHub exige une approbation d'environnement, la traiter dans l'exécution Actions concernée.

Vérifier le SHA du workflow production, sa réussite, puis les parcours essentiels sur <https://cinestats5050.fr>. Le workflow reconstruit les images avec les réglages de production ; il ne réutilise pas les images preview.

## Comprendre les options et les échecs

| Situation | Comportement et suite à donner |
| --- | --- |
| Sans `--watch` | Le script termine après le push. Cela ne confirme pas la réussite du déploiement. Consulter Actions. |
| Branche déjà au même commit | Le script termine sans push ni nouveau workflow, même avec `--watch`. Vérifier le dernier déploiement ; utiliser le lancement manuel du workflow si un redéploiement est nécessaire. |
| Historique divergent | La promotion est refusée : la cible contient des commits absents de `main`. Examiner l'historique avant toute action. |
| `--force` | Ignore la protection de fast-forward et force le push. Des commits propres à la cible peuvent sortir de son historique. Ce n'est pas une étape normale de promotion. |
| Workflow introuvable après le push | Le push peut avoir réussi. Consulter Actions avant de relancer ; l'échec du suivi n'annule pas le push. |
| Déploiement en échec | Examiner les logs du workflow. Ne pas poursuivre vers production après un échec preview. |

Pour examiner les commits propres à la preview :

```bash
git log origin/main..origin/preview --oneline
```

Pour retrouver une exécution après un échec du suivi automatique :

```bash
gh run list --repo Le-Collectif-50-50/cinestats-5050 \
  --branch preview --workflow Deploy --limit 5
```

Remplacer `preview` par `production` pour examiner cet environnement. Pour revenir à une version déjà déployée, suivre la [procédure de rollback](../DEPLOYMENT.md#rollback). Un rollback applicatif n'annule pas les migrations de données.
