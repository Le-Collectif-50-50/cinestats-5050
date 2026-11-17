# Dépanner les timeouts et fermetures du navigateur Allociné

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-13

**Status:** actif

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-16 | Joel Teixeira | Gestion des fermetures et nettoyage des ressources du navigateur. |
| 2 | 2026-11-13 | Joel Teixeira | Diagnostic par type de timeout, navigation DOMContentLoaded et reprise bornée existante. |

## Identifier le délai concerné

Le [guide Allociné](../../ingestion/scraping/allocine/README.md#délais-et-timeouts) décrit les paramètres et les budgets. Activer `verbose: true` et conserver `parallel_sessions: 1` pour observer un lot limité.

| Message | Vérification |
| --- | --- |
| `Navigation timed out after ...` | Vérifier l’URL et la durée. `navigation_timeout_seconds` vaut 60 s par défaut. |
| `Record timed out after ...` | Le budget du film inclut fiche, casting et interactions. `record_timeout_seconds` vaut 240 s ; la recherche sans ID dispose de six fois ce budget. |
| Erreur `connect_over_cdp` | Vérifier l’accès worker → Browserless, le DNS Docker et la santé du service. Le délai de connexion est indépendant du délai de page. |
| `Browser connection lost` / `Target page, context or browser has been closed` | Vérifier les logs Browserless, la mémoire, le CPU et la durée de session. Compose fixe `CONNECTION_TIMEOUT=600000`, soit dix minutes. |
| HTTP 403/429 ou page de blocage | Augmenter le délai ne résout pas le blocage. Le résultat reste `blocked`. |

Les messages identifient une étape en échec ; ils ne prouvent pas à eux seuls la cause de l’incident.

## Comportement actuel

La navigation Allociné attend `DOMContentLoaded`, puis effectue les interactions avant extraction du HTML. Elle n’attend plus `networkidle`, condition sensible aux requêtes publicitaires persistantes. Augmenter le délai aide seulement lorsque la page finit par répondre. Les configurations personnalisées peuvent surcharger les délais.

Le connecteur réouvre une session et retente une fois un film après timeout ou fermeture reconnue. Après deux tentatives, l’échec est conservé en base ; le film reste rééligible lors d’un prochain run. Chaque tentative possède son propre budget. Le backfill des affiches garde une session et une tentative par candidat.

`AsyncBrowserSession.__aexit__` tente séparément la fermeture de la page, du contexte, du navigateur et de Playwright. Une erreur de fermeture n’empêche pas les nettoyages suivants. Cela ne garantit pas que la session restera disponible pendant le scraping.

## Vérifier après livraison

1. Attendre la fin des runs actifs avant de recréer le worker.
2. Publier puis lancer le [déploiement manuel Allociné](../../ingestion/README.md#publier-et-lancer-le-scraping-seul).
3. Examiner les succès, les messages d’échec et les durées sur un lot comparable.
4. Pour une fermeture proche de dix minutes, examiner la limite de session Browserless avant d’augmenter le délai de navigation.

Les tests sans réseau sont dans `tests/ingestion/test_allocine_timeouts.py`. Ils vérifient la lecture sans attente réseau, les délais configurés, les blocages HTTP et la reprise limitée à deux tentatives. Ils ne mesurent pas la disponibilité réelle d’Allociné.
