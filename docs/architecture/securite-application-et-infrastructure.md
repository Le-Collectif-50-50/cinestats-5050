# Sécurité de CinéStats 50-50 : mesures en place

**Owner:** Nicolas Revel
**Dernière révision:** 2026-11-17
**Status:** brouillon

## Objet et périmètre

Ce document décrit comment l'application CinéStats 50-50 (projet RIC, porté par le Collectif 50-50) est sécurisée. Il s'adresse aux partenaires du Collectif, notamment au CNC.

Deux versions coexistent. Le Collectif diffuse et amende un Google Doc destiné aux partenaires. Ce fichier en est la source technique, versionnée avec le code : toute évolution de l'infrastructure ou du code qui touche la sécurité le met à jour dans la même PR. Reporter ensuite le changement dans le Google Doc, et inversement.

Il ne décrit que des mesures **présentes dans le code et la configuration** du dépôt. Chaque mesure renvoie au fichier qui la met en œuvre. Le dépôt définit la configuration, mais il ne prouve pas que chaque serveur l'applique aujourd'hui. Les points qui demandent une vérification sur les serveurs ou dans l'espace client OVH sont signalés par **[À vérifier]** et regroupés dans la section « Points à vérifier ».

Périmètre :

- l'application publique : site `cinestats5050.fr` et API `api.cinestats5050.fr` ;
- les trois VPS de production `app`, `db` et `data`, ainsi que la chaîne de déploiement GitHub Actions ;
- hors périmètre : les serveurs Metabase, Services (Prometheus, Grafana, Authentik) et preview. Ils sont configurés en partie dans le dépôt `cinestats-infra`, qui n'a pas été audité ici.

## Synthèse

| Domaine | Responsable | Mesures principales |
| --- | --- | --- |
| Datacenter, matériel, hyperviseur, réseau amont | OVHcloud | Sécurité physique, virtualisation, protection anti-DDoS du réseau OVH **[À vérifier]** |
| Compte OVH | Équipe projet | Double authentification, nombre de comptes limité **[À vérifier]** |
| Système des VPS | Équipe projet | Pare-feu à refus par défaut, SSH par clé seule, fail2ban, mises à jour de sécurité automatiques, durcissement du noyau |
| Réseau interne | Équipe projet | Tunnel WireGuard chiffré vers la base, base de données invisible depuis Internet |
| Base de données | Équipe projet | Moindre privilège par rôle, TLS, accès en lecture seule pour l'API, sauvegardes chiffrées hors site |
| Application | Équipe projet | HTTPS obligatoire, limitation du débit par IP, API en lecture seule, requêtes SQL paramétrées, conteneurs sans root |
| Développement et déploiement | Équipe projet | Revue obligatoire des PR, audit des dépendances Python, secrets hors du code, déploiement en production soumis à approbation |

## Architecture

```
                Internet
                   │
     80/443 ───────┼────────── SSH 22022 (clé seule) sur chaque VPS
                   ▼
   ┌────────────────────────┐        ┌──────────────────────────┐
   │ VPS app (France)       │        │ VPS data (Canada)        │
   │ nginx → frontend       │        │ Airbyte, Prefect, dbt,   │
   │       → backend (API)  │        │ scrapers                 │
   └───────────┬────────────┘        │ 80/443 : Caddy → SSO     │
               │                     │ Authentik → Airbyte      │
               │  WireGuard          └────────────┬─────────────┘
               │  10.50.0.0/24 (chiffré)          │
               ▼                                  ▼
          ┌──────────────────────────────────────────┐
          │ VPS db (France) : PostgreSQL 16          │
          │ n'écoute que sur localhost et le tunnel  │
          │ sauvegardes pgBackRest locales + hors    │
          │ site (OVH Object Storage, chiffrées)     │
          └──────────────────────────────────────────┘
```

Le service qui reçoit les visiteurs (`app`) est séparé de celui qui stocke les données (`db`). La base de données n'est pas joignable depuis Internet. `app` et `data` n'ont pas de route l'un vers l'autre dans le tunnel.

Sources : [runbook de sécurisation des VPS](../runbooks/securisation-vps-prod.md), [guide de déploiement](../DEPLOYMENT.md), [runbook stack data](../runbooks/stack-data.md).

## 1. Ce qui relève d'OVHcloud

Les trois VPS de production et le stockage des sauvegardes hors site sont hébergés chez OVHcloud. Une part de la sécurité dépend donc de l'hébergeur, et l'équipe n'a pas la main dessus.

| Domaine | Ce que couvre OVHcloud | Statut |
| --- | --- | --- |
| Sécurité physique | Accès aux datacenters, alimentation, refroidissement, incendie | Responsabilité OVH, selon son offre |
| Matériel et virtualisation | Serveurs physiques, hyperviseur, isolation entre VPS clients | Responsabilité OVH |
| Réseau amont | Connectivité, protection anti-DDoS du réseau OVH | **[À vérifier]** : l'inclusion et le niveau de la protection anti-DDoS de l'offre VPS souscrite, à confirmer dans l'espace client |
| Edge Network Firewall | Filtrage optionnel en amont des VPS, configurable dans l'espace client | **[À vérifier]** : le runbook le présente comme optionnel ; son activation n'est pas confirmée |
| Stockage des sauvegardes | OVH Object Storage (S3), dans une autre région que la base | Utilisé, voir §4.3 |
| DNS et API OVH | Zone DNS des domaines, utilisée pour émettre les certificats TLS | Utilisé, voir §5.1 |
| Console KVM | Accès de secours aux VPS depuis l'espace client | Disponible |
| Localisation | `app` et `db` en France, `data` au Canada | **[À vérifier]** : datacenters exacts |
| Certifications | Certifications de sécurité d'OVHcloud | **[À vérifier]** : lister celles qui couvrent l'offre VPS utilisée, avant de les citer à un partenaire |

**Côté équipe, sur le compte OVH :** le runbook demande d'activer la double authentification et de limiter les comptes qui ont accès à l'espace client. Quiconque contrôle ce compte peut réinstaller ou supprimer les VPS. **[À vérifier]** dans l'espace client.

Tout ce qui suit est mis en place et maintenu par l'équipe projet.

## 2. Système des VPS (géré par l'équipe)

Les trois VPS sont installés en Debian, puis durcis par les scripts de [`infra/vps/`](../../infra/vps/). Ces scripts sont versionnés et peuvent être rejoués sans risque.

### 2.1 Pare-feu : tout est fermé par défaut

Source : [`infra/vps/00-base.sh`](../../infra/vps/00-base.sh), [`20-docker.sh`](../../infra/vps/20-docker.sh), [`10-wireguard.sh`](../../infra/vps/10-wireguard.sh), [`30-postgres.sh`](../../infra/vps/30-postgres.sh), [`55-exporters.sh`](../../infra/vps/55-exporters.sh), [`60-caddy.sh`](../../infra/vps/60-caddy.sh).

- `ufw` refuse tout le trafic entrant par défaut. Seuls les ports listés ci-dessous sont ouverts.
- **Correction d'une faille connue de Docker.** Docker publie ses ports sans passer par `ufw`. Un service `systemd` (`cinestats-docker-user-firewall`) filtre donc la chaîne `DOCKER-USER`, en IPv4 et IPv6. Sur `app`, seuls les ports 80 et 443 des conteneurs sont joignables depuis Internet. Sur `data`, aucun port de conteneur ne l'est.

| VPS | Ports ouverts depuis Internet | Ports ouverts à une seule source |
| --- | --- | --- |
| `app` | 80 (redirection vers HTTPS), 443, SSH 22022 | 9100 (métriques) : IP du serveur Prometheus seulement |
| `db` | SSH 22022 | 51820/UDP (WireGuard) : IP de `app` et `data` seulement ; 9100 : Prometheus seulement |
| `data` | SSH 22022 ; 80 et 443 (Caddy, accès web à Airbyte derrière SSO, voir §2.5) | 9100 : Prometheus seulement |

Les interfaces d'administration de `data` (Airbyte 8000, Prefect 4222, navigateur headless 3000) restent filtrées. Prefect n'est joignable que par tunnel SSH.

Le runbook prévoit un contrôle par `nmap -Pn -p- <IP>` depuis l'extérieur. **[À vérifier]** : le relancer sur les trois VPS et archiver le résultat.

### 2.2 Accès administrateur par SSH

Source : [`infra/vps/files/ssh/10-cinestats.conf`](../../infra/vps/files/ssh/10-cinestats.conf).

- Port 22022 au lieu de 22.
- Authentification **par clé uniquement** : mot de passe et clavier interactif désactivés.
- Connexion directe en `root` interdite. Seuls les comptes du groupe `ssh-users` peuvent se connecter.
- 3 tentatives d'authentification au plus par connexion, 30 secondes pour s'authentifier.
- Transfert X11, transfert d'agent et tunnels réseau désactivés. Les redirections de port locales ne sont autorisées que sur `data`, pour les tunnels d'administration.
- Les sessions inactives sont coupées après 10 minutes environ.
- Le script de mise en place teste une deuxième connexion avant d'appliquer la configuration, et revient en arrière en cas d'échec.

SSH reste ouvert sur Internet, car les runners GitHub Actions n'ont pas d'adresse IP fixe. Les clés seules, fail2ban et l'environnement GitHub protégé compensent cette exposition.

### 2.3 fail2ban : blocage des attaques par force brute sur SSH

Source : [`infra/vps/files/fail2ban/cinestats-sshd.local`](../../infra/vps/files/fail2ban/cinestats-sshd.local).

fail2ban est installé et activé sur les trois VPS, avec une prison `sshd` sur le port 22022 :

- bannissement après **5 échecs en 10 minutes** ;
- bannissement initial d'**1 heure**, **allongé à chaque récidive**, jusqu'à **1 semaine** ;
- lecture du journal `systemd` (Debian n'a plus `/var/log/auth.log` par défaut).

fail2ban ne protège que SSH. Le trafic web est limité par nginx (voir §5.2).

### 2.4 Mises à jour et durcissement du système

Sources : [`00-base.sh`](../../infra/vps/00-base.sh), [`files/apt/`](../../infra/vps/files/apt/), [`files/sysctl/99-cinestats.conf`](../../infra/vps/files/sysctl/99-cinestats.conf), [`files/docker/daemon.json`](../../infra/vps/files/docker/daemon.json).

- **Mises à jour de sécurité automatiques** (`unattended-upgrades`), y compris pour PostgreSQL (dépôt officiel `apt.postgresql.org`). Si une mise à jour l'exige, le serveur redémarre automatiquement la nuit : 04:00 (`db`), 04:30 (`data`) ou 05:00 (`app`), à des heures décalées.
- Les mises à jour hors sécurité (Docker, etc.) sont appliquées à la main chaque mois, selon le runbook.
- **Paramètres réseau du noyau** : filtrage anti-usurpation d'adresse (`rp_filter`), redirections ICMP et routage par la source refusés, protection SYN cookies, accès restreint aux adresses et aux messages du noyau (`kptr_restrict`, `dmesg_restrict`).
- **Docker** est installé depuis le dépôt officiel, avec signature vérifiée. Ses journaux sont plafonnés et l'option `no-new-privileges` est active sur `app`.
- **Journal système** persistant, plafonné à 500 Mo. Horloge synchronisée par NTP, utile pour dater les événements.
- Caddy (sur `data`) est installé depuis la release officielle, avec vérification de l'empreinte SHA-512.
- Après un redémarrage automatique, les services repartent seuls : conteneurs en `restart: unless-stopped`, y compris Prefect sur `data` ([runbook stack data](../runbooks/stack-data.md), reprise après le reboot de 04:30).

### 2.5 Accès aux outils internes de la stack data

Source : [runbook stack data §6](../runbooks/stack-data.md), [`infra/data/authentik-outpost/docker-compose.yml`](../../infra/data/authentik-outpost/docker-compose.yml).

L'outil d'ingestion Airbyte n'est jamais exposé directement. Le chemin d'accès est le suivant : navigateur → Caddy (HTTPS, Let's Encrypt) → proxy Authentik (authentification unique, réservée au groupe « Airbyte Admins ») → Airbyte, qui exige en plus son propre mot de passe. Le proxy et Airbyte n'écoutent qu'en local.

### 2.6 Supervision

Sources : [`50-monitoring.sh`](../../infra/vps/50-monitoring.sh), [`55-exporters.sh`](../../infra/vps/55-exporters.sh), runbook §7.

- Une alerte (healthchecks.io) part si un disque dépasse 80 %, ou si une sauvegarde échoue ou n'a pas lieu.
- Les métriques système sont collectées par Prometheus et affichées dans Grafana.
- Limite : la panne d'un VPS se voit dans Grafana mais ne déclenche pas d'alerte. La surveillance de disponibilité externe du site est prévue par le runbook. **[À vérifier]** : sa mise en place.

## 3. Réseau interne (géré par l'équipe)

Source : [`infra/vps/10-wireguard.sh`](../../infra/vps/10-wireguard.sh).

- Les VPS communiquent avec la base par un tunnel **WireGuard** chiffré (`10.50.0.0/24`), dont `db` est le point central.
- Chaque pair n'est autorisé qu'avec sa propre adresse. `app` et `data` ne se voient pas l'un l'autre.
- Le port WireGuard de `db` n'accepte que les adresses IP publiques des pairs déclarés.

## 4. Base de données (gérée par l'équipe)

Sources : [`infra/vps/30-postgres.sh`](../../infra/vps/30-postgres.sh), [`infra/vps/sql/roles.sql`](../../infra/vps/sql/roles.sql), [`files/postgresql/`](../../infra/vps/files/postgresql/).

### 4.1 Exposition et chiffrement

- PostgreSQL 16 n'écoute que sur `localhost` et sur l'adresse du tunnel. Il n'écoute pas sur l'IP publique.
- TLS activé (version 1.2 minimum). Mots de passe stockés en `scram-sha-256`.
- `pg_hba.conf` fonctionne en liste blanche « rôle × base × IP source ». Toute autre connexion est rejetée explicitement.
- Chaque connexion est journalisée avec son adresse IP source.

### 4.2 Moindre privilège

Chaque composant a son propre rôle, limité à ce dont il a besoin :

| Rôle | Utilisé par | Droits |
| --- | --- | --- |
| `app_ro` | API publique | `SELECT` sur le schéma de l'application, transactions forcées en lecture seule, requêtes limitées à 10 s, 20 connexions au plus |
| `app_migrator` | Migrations, lancées à la main | Propriétaire du schéma ; son mot de passe n'est jamais stocké sur un serveur |
| `airbyte_user`, `dbt_user`, `scraper_user`, `prefect_user` | Stack data | Limités à leurs schémas d'ingestion ; aucun droit sur les tables de l'application |
| `metabase_user` | Tableaux de bord | Lecture seule de la couche finale |
| `metabase_ops_user` | Tableaux de bord d'exploitation | Lecture de toutes les couches, écriture dans `ops` seulement |

Aucun droit implicite n'est donné à `PUBLIC` sur la base. L'API publique ne peut donc ni modifier ni supprimer de données, même si elle était compromise.

### 4.3 Sauvegardes et restauration

Sources : [`infra/vps/40-pgbackrest.sh`](../../infra/vps/40-pgbackrest.sh), [`files/pgbackrest/`](../../infra/vps/files/pgbackrest/).

- **pgBackRest** avec archivage continu des journaux de transactions : au plus **15 minutes de données perdues**.
- Sauvegarde complète le dimanche, différentielle les autres jours.
- **Deux dépôts** :
  - local, conservé 2 semaines ;
  - hors site, dans OVH Object Storage, dans une **autre région**, **chiffré** et conservé 4 semaines. L'utilisateur S3 n'a accès qu'à ce bucket.
- La restauration est testée dès la mise en place, puis chaque mois selon le runbook.
- Une alerte part si une sauvegarde échoue.

## 5. Application (gérée par l'équipe)

### 5.1 HTTPS et en-têtes de sécurité

Sources : [`nginx/prod.conf`](../../nginx/prod.conf), [`docker-compose.prod.yaml`](../../docker-compose.prod.yaml), [`certbot/`](../../certbot/).

- Tout le trafic HTTP est redirigé vers HTTPS.
- TLS 1.2 et 1.3 uniquement, avec des suites de chiffrement ECDHE-AES-256-GCM.
- Certificats Let's Encrypt, émis et renouvelés automatiquement (vérification toutes les 12 h) par validation DNS via l'API OVH.
- En-têtes envoyés : `Strict-Transport-Security` (HSTS, 1 an, sous-domaines inclus), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`.
- nginx est le seul service exposé. Le frontend et le backend ne sont joignables que sur le réseau Docker interne.

### 5.2 Limitation du débit (rate limiting)

Source : [`nginx/prod.conf`](../../nginx/prod.conf), ajoutée par la [PR #36](https://github.com/Le-Collectif-50-50/cinestats-5050/pull/36). **[À vérifier]** : effective une fois la PR fusionnée et déployée en production.

L'API étant en lecture seule et sans compte, un abus ne menace pas les données. Il menace la disponibilité : un seul client qui interroge l'API en boucle pourrait occuper toutes les connexions à la base et ralentir le site pour tout le monde. nginx limite donc le nombre de requêtes par adresse IP :

| Cible | Débit par IP | Marge tolérée |
| --- | --- | --- |
| API | 10 requêtes/s | 30 requêtes |
| Pages du site | 20 requêtes/s | 60 requêtes, pour le préchargement des liens par Next.js |
| Fichiers statiques (scripts, styles, images) | Non limités | – |

- Au-delà, nginx répond `429 Too Many Requests` et l'inscrit dans son journal.
- Ces seuils sont larges, pour ne pas gêner plusieurs visiteurs qui partagent une même adresse IP (école, bureau).
- Les adresses privées (réseau interne Docker) ne sont pas limitées, pour ne pas regrouper plusieurs clients dans un même compteur.
- La base ajoute ses propres garde-fous : l'API dispose de 20 connexions au plus, et chaque requête est coupée au bout de 10 s.
- Cette limitation complète la protection anti-DDoS d'OVH, qui agit au niveau réseau mais laisse passer des requêtes HTTP valides envoyées en masse.

### 5.3 API

Sources : [`backend/main.py`](../../backend/main.py), [`backend/routers/`](../../backend/routers/), [`backend/repositories/`](../../backend/repositories/).

- L'API publique n'expose que des routes `GET`, sans compte utilisateur ni saisie de données personnelles.
- Les paramètres sont typés et validés par FastAPI (identifiants entiers, recherche non vide).
- Les requêtes SQL passent par l'ORM SQLAlchemy et sont donc paramétrées : pas de concaténation de chaînes, ce qui protège contre l'injection SQL.
- CORS limité à une liste d'origines explicites (`ALLOWED_ORIGINS`).
- Les tableaux Metabase intégrés au site utilisent un jeton signé (HS256), valable 10 minutes, et généré côté serveur. La clé de signature ne quitte pas le backend.

### 5.4 Conteneurs

Sources : [`backend/Dockerfile.prod`](../../backend/Dockerfile.prod), [`frontend/Dockerfile.prod`](../../frontend/Dockerfile.prod).

- Le backend et le frontend tournent avec un utilisateur **non root** (`app` et `node`).
- Les images de production sont construites par la CI et publiées sur GitHub Container Registry, avec un tag par environnement et par commit.
- Chaque service a un contrôle de santé. Un déploiement dont un service ne devient pas sain revient automatiquement à la version précédente.

## 6. Développement et déploiement (gérés par l'équipe)

Sources : [`.github/workflows/`](../../.github/workflows/), [guide de déploiement](../DEPLOYMENT.md), [`.gitignore`](../../.gitignore).

### 6.1 Gestion du code

- Les modifications passent par des pull requests vers `main`, avec **une approbation obligatoire**.
- Une version est d'abord validée en préproduction (`preview`, sur une machine distincte), puis promue en production.
- Contrôles automatiques à chaque PR : linter Python (`ruff`) et **audit des vulnérabilités des dépendances Python** (`pip-audit`). Une alerte de cet audit a par exemple conduit à corriger la dépendance SoupSieve.
- **Seule exception à la revue :** le workflow [`dbt-lineage.yml`](../../.github/workflows/dbt-lineage.yml) publie lui-même `docs/dbt-lineage.md` sur `main` après chaque fusion touchant l'ingestion. Il utilise une GitHub App dont le token est créé à chaque exécution, limité à ce dépôt et au droit d'écriture du contenu. Le job ne publie que ce fichier, et renonce si les sources ont changé entre-temps. Le job de génération n'a qu'un droit de lecture et ne conserve pas les identifiants de checkout.
- Les fichiers `.env` sont exclus de git. Aucun secret n'est versionné.

### 6.2 Secrets et déploiement

- Les secrets (accès base, clé SSH de déploiement, clés Metabase et OVH) sont stockés dans les **environnements GitHub** `preview` et `production`. Ils ne sont pas dans le code.
- L'environnement `production` exige l'**approbation d'un reviewer** et n'accepte que la branche `production`.
- Le workflow ne donne à chaque job que les permissions dont il a besoin (`permissions: {}` par défaut).
- La clé d'hôte SSH du serveur est **épinglée** (`SSH_KNOWN_HOSTS`). Un serveur usurpé fait échouer le déploiement au lieu de recevoir les secrets.
- Le fichier `.env` du serveur est régénéré à chaque déploiement, transmis par l'entrée standard, avec des droits `600`. Les secrets n'apparaissent dans aucune ligne de commande.
- Le compte `deploy` du VPS `app` n'a pas `sudo`. Les migrations de schéma ne sont jamais automatiques en production.

## 7. Limites connues et écarts assumés

Ces points sont documentés dans les runbooks ou constatés dans le code. Ils sont listés ici pour que le document reste exact.

| Point | Détail | Impact |
| --- | --- | --- |
| Compte `ubuntu` partagé avec `sudo` sans mot de passe | Choix d'exploitation. Toutes les personnes habilitées se connectent avec le même compte. Seule l'empreinte de la clé SSH, dans le journal, identifie la personne. | Le vol d'une clé autorisée donne un accès root. Les clés doivent être protégées par une phrase de passe, sur des disques chiffrés. |
| Compte `deploy` équivalent à root sur `app` | Il appartient au groupe `docker`. | Sa clé n'existe que dans le secret GitHub protégé. |
| `dbt_user` accepte les connexions sans TLS | Les scrapers forcent encore `sslmode=disable`. | Le trafic reste chiffré par WireGuard. |
| Certificat PostgreSQL auto-signé | Les clients chiffrent sans vérifier l'identité du serveur. | Acceptable à l'intérieur du tunnel WireGuard. |
| Publication automatique sur `main` | La GitHub App de `dbt-lineage.yml` peut écrire dans le dépôt sans revue. Sa clé privée est un secret GitHub. | Limité par le workflow au seul fichier de lineage. **[À vérifier]** : l'App n'est installée que sur ce dépôt, et son éventuel contournement de la protection de `main` ne sert qu'à ce workflow. |
| 5 vulnérabilités ignorées par `pip-audit` | `starlette`, dépendance de FastAPI : aucun correctif n'est compatible avec FastAPI pour l'instant. | À lever dès qu'une version compatible sort. |
| Contrôles frontend partiels | Le workflow frontend n'installe que les dépendances. Lint, vérification de types et tests sont désactivés. Aucun audit des dépendances JavaScript. | Moins de garde-fous automatiques côté interface. |
| En-têtes de sécurité incomplets | Pas de `Content-Security-Policy`. Sur les fichiers statiques (images, CSS, JS), le `add_header Cache-Control` du bloc `location` remplace les en-têtes du serveur : HSTS, `nosniff` et `X-Frame-Options` n'y sont pas envoyés. Le fichier commun `nginx/security-headers.conf` n'est inclus qu'en preview : la production répète ces en-têtes dans `prod.conf`. | Faible, mais facile à corriger. |
| Alerte de disponibilité | La panne d'un VPS ne déclenche pas d'alerte automatique (voir §2.6). | Délai de détection d'une panne. |
| Données personnelles au Canada | Le VPS `data` traite des noms et le genre de professionnels du cinéma. Le Canada bénéficie d'une décision d'adéquation de l'UE ; le traitement doit figurer au registre RGPD. | **[À vérifier]** : inscription au registre. |

## 8. Points à vérifier avant diffusion

Le dépôt décrit la configuration attendue. Pour l'attester auprès d'un partenaire, vérifier sur les serveurs et dans l'espace client OVH :

1. **Limitation de débit** : PR #36 fusionnée et déployée en production ; aucun `429` en navigation normale (`docker compose logs nginx | grep 'limiting requests'`).
2. **Pare-feu et ports**, sur chaque VPS : `sudo ufw status verbose`, `sudo iptables -S DOCKER-USER`. Depuis l'extérieur : `nmap -Pn -p- <IP>`.
3. **fail2ban** : `sudo fail2ban-client status sshd` sur chaque VPS.
4. **SSH** : `sudo sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|allowgroups) '`.
5. **Mises à jour automatiques** : `sudo unattended-upgrade --dry-run --debug`.
6. **Sauvegardes** : `sudo -u postgres pgbackrest --stanza=main info` sur `db` (deux dépôts, `status: ok`), et date du dernier test de restauration.
7. **TLS** : note obtenue sur SSL Labs pour `cinestats5050.fr` et `api.cinestats5050.fr`.
8. **OVH** : double authentification sur le compte, liste des personnes qui y ont accès, protection anti-DDoS de l'offre, état de l'Edge Network Firewall, datacenters exacts, certifications applicables à l'offre VPS.
9. **GitHub** : reviewer obligatoire et restriction de branche sur l'environnement `production`, approbation obligatoire sur `main`, périmètre et droits de la GitHub App `dbt-lineage`.
10. **Surveillance de disponibilité externe** : service en place et destinataires des alertes.
11. **RGPD** : traitement inscrit au registre.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-09 | Nicolas Revel | Première version : mesures vérifiées dans le dépôt, séparation OVH / équipe, limitation de débit nginx (PR #36), limites et points à vérifier sur les serveurs. |
| 2 | 2026-11-17 | Nicolas Revel | Alignement sur `main` : publication automatique du lineage dbt, correctif SoupSieve, reprise de Prefect après reboot. Articulation avec le Google Doc du Collectif. |
