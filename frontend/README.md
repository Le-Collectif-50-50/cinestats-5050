# Objectif 50 / 50 frontend

## Metadata du document

**Owner:** Nicolas Revel

**Last reviewed:** 2026-10-09

**Status:** active

## Historique du document

| #   | Date       | Author        | Observations           |
| --- | ---------- | ------------- | ---------------------- |
| 1   | 2026-05-07 | Joel Teixeira | Initial implementation |
| 2   | 2026-10-09 | Joel Teixeira | Fond partagé avec sélection AVIF, WebP et repli JPEG |

## Prérequis

- Node.js (v20 ou plus récent)
- pnpm (Gestionnaire de paquets)

## Installation de pnpm

```bash
# Installer pnpm globalement
npm install -g pnpm

# Vérifier l'installation
pnpm --version
```

## Configuration du Projet

1. Installer les dépendances :

```bash
pnpm install
```

2. Démarrer le serveur de développement :

```bash
pnpm dev
```

L'application sera disponible sur [http://localhost:3000](http://localhost:3000).

## Dépendances du Projet

Les dépendances principales incluent :

- Next.js 15
- React 19
- TypeScript
- TailwindCSS (pour le style)
- shadcn/ui (pour les composants UI)

## Structure du Projet

```text
├── app/            # Routes de l'application Next.js
├── components/     # Composants React réutilisables
├── public/         # Ressources statiques
└── styles/        # Styles globaux
```

## Bases de Next.js

Next.js est un framework React qui fournit :

- Rendu côté serveur
- Génération de sites statiques
- Routes API
- Routage basé sur les fichiers
- Optimisation intégrée

### Fonctionnalités Principales

- Les pages sont créées dans le répertoire `app`
- Les routes API sont définies dans `app/api`
- Les ressources statiques vont dans le répertoire `public`
- Fractionnement automatique du code
- Remplacement à chaud des modules

## Image de fond

Les pages d’accueil (`/`) et de présentation (`/about`) utilisent le composant
`src/components/atoms/BackgroundImage.tsx`. Son élément `<picture>` propose,
dans cet ordre, `public/home.avif`, `public/home.webp`, puis `public/home.jpg`.
Le navigateur sélectionne le premier format pris en charge. Ce repli concerne
la compatibilité des formats, pas les erreurs HTTP : les trois fichiers doivent
être présents lors du déploiement.

Les variantes conservent la résolution de 1920 × 1013 pixels. Le JPEG original
pèse environ 1 992 kB, le WebP (qualité 90) 311 kB et l’AVIF (qualité 80) 287 kB.
Ces deux variantes utilisent une compression avec perte ; elles ne sont pas
strictement identiques au JPEG décodé. Le fond conserve son opacité de 0,3,
son cadrage en haut et son positionnement fixe. L’image est décorative et son
chargement est immédiat, avec une priorité élevée.

Pour vérifier localement, ouvrir `/` et `/about`, puis filtrer les requêtes réseau
sur `home.` : un navigateur compatible AVIF doit charger `home.avif` sans charger
également les variantes WebP et JPEG. Vérifier le cadrage sur mobile et ordinateur.
Pour contrôler les replis dans les outils de développement, retirer temporairement
la source AVIF, puis la source WebP : l’image doit rester visible avec le format
suivant. Cette manipulation vérifie la chaîne de sélection ; elle ne remplace pas
un test sur un ancien navigateur.

## Guide de Développement

1. Respecter le système de types TypeScript
2. Utiliser des composants pour les éléments UI réutilisables
3. Garder les pages dans le répertoire app
4. Suivre les bonnes pratiques Next.js
5. Utiliser les composants shadcn/ui pour un design cohérent

Pour plus de détails, consultez la [documentation Next.js](https://nextjs.org/docs).

## Referenced by

- [README.md](../README.md)
