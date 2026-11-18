# Suivre les statuts des issues GitHub

**Owner:** Joel Teixeira
**Dernière révision:** 2026-11-18
**Status:** actif

Le workflow [Issue status](../../.github/workflows/issue-status.yml) synchronise les labels d’avancement des issues avec leurs PR liées. Les labels de domaine (`dbt`, `bug`, etc.) et les responsables restent inchangés. Les quatre labels `statut: à faire`, `statut: en cours`, `statut: à valider` et `statut: bloqué` doivent exister dans le dépôt.

## Lier une PR à une issue

Dans la description de la PR ciblant la branche par défaut, écrire `Fixes #41` ou `Closes #41`. GitHub crée le lien natif et ferme automatiquement l’issue lors de la fusion. Pour plusieurs issues, répéter le mot-clé : `Fixes #41, fixes #42`.

Un lien manuel via la rubrique **Development** est également reconnu. Une simple mention `#41` n’est pas suffisante. Les liens vers les issues d’autres dépôts sont ignorés.

## Transitions appliquées

| Situation actuelle | Résultat |
| --- | --- |
| Issue fermée, notamment par fusion avec `Fixes` | Suppression des labels `statut: …` ; l’issue reste fermée |
| Issue ouverte avec `statut: bloqué` | Blocage manuel conservé |
| Au moins une PR liée ouverte, même en brouillon | `statut: en cours` |
| Aucune PR liée ouverte, mais au moins une fusionnée | `statut: à valider` |
| Toutes les PR liées fermées sans fusion, ou issue rouverte sans PR | `statut: à faire` |

La fusion ne prouve pas le déploiement ni la validation métier. Une issue laissée ouverte reste donc à valider. GitHub conserve sa clôture automatique pour les liens de résolution ; le workflow ne ferme et ne rouvre aucune issue. Le blocage se lève manuellement avant une nouvelle synchronisation.

Les événements d’ouverture, réouverture, modification, ajout de commits, passage en revue/brouillon et fermeture de PR déclenchent le workflow. Les fermetures et réouvertures d’issues le déclenchent aussi. L’état des PR est relu au moment de l’exécution pour traiter les événements retardés et les issues associées à plusieurs PR.

## Relancer après un lien manuel

L’ajout ou le retrait d’un lien via **Development** ne déclenche pas nécessairement d’événement de PR. Après ajout, ouvrir **Actions → Issue status → Run workflow**, sélectionner la branche par défaut et renseigner le numéro de PR. En CLI :

```bash
gh workflow run issue-status.yml --ref main -f pr_number=50
```

La relance traite les liens présents à cet instant. Après suppression d’un lien, ajuster manuellement le statut de l’issue détachée ; elle n’appartient plus au périmètre de cette PR. Les issues sans PR liée ne sont pas parcourues globalement. Le workflow devient actif une fois intégré dans la branche par défaut ; il ne reprend pas automatiquement les événements antérieurs.

## Permissions et vérification

Le workflow utilise `GITHUB_TOKEN` avec `issues: write`, `pull-requests: read` et `contents: read`, sans secret supplémentaire. Il charge uniquement le code du commit du workflow, jamais celui de la branche proposée par une PR. Les descriptions et titres de PR ne sont pas exécutés. Les exécutions sont sérialisées avec une file de 100 exécutions en attente au maximum (`queue: max`). Relancer avec le numéro de PR si un événement n’a pas été traité.

Vérification locale du script, sans écriture GitHub :

```bash
node --test .github/scripts/issue-status.test.cjs
```

Le workflow `Issue status checks` exécute aussi ces tests sur les PR et les changements de `main` concernant cette automatisation, avec des permissions de lecture uniquement.

En cas d’échec, consulter le journal du workflow : un label absent ou une erreur API fait échouer l’exécution. Corriger la cause puis relancer. Après activation, vérifier sur une PR liée l’ajout de `statut: en cours`, puis la suppression des statuts après clôture automatique ou le passage à `statut: à valider` si l’issue reste ouverte.

Références : [liens PR–issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue), [événements GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-18 | Joel Teixeira | Synchronisation des statuts par liens natifs PR–issues et procédure de relance. |
