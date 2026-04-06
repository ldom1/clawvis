# Clawvis — Documentation

**Clawvis** est un hub self-hosted de pilotage d’agents IA : Kanban, Brain (mémoire / Quartz), runtime IA, logs — stack documentée dans ce dossier.

**Dépôt source** : [github.com/ldom1/clawvis](https://github.com/ldom1/clawvis).

> **Wiki GitHub (miroir)** — Cette documentation est [synchronisée automatiquement](https://github.com/ldom1/clawvis/actions/workflows/sync-wiki.yml) depuis `docs/` vers le [wiki](https://github.com/ldom1/clawvis/wiki). **Ne pas éditer le wiki directement** : toute modification passe par les fichiers Markdown dans [`docs/`](https://github.com/ldom1/clawvis/tree/main/docs) sur le dépôt principal. Le contenu est **aplati** à la racine du wiki (pas de sous-dossiers) ; les liens relatifs du dépôt sont fiables en local / sur GitHub, pas toujours dans l’UI wiki — voir [Correspondance wiki](#correspondance-wiki-fichiers-aplatis). Si le workflow ne peut pas pousser vers le wiki, ajouter un secret dépôt `WIKI_SYNC_TOKEN` (PAT avec scope `repo`).

> Index de navigation. Tous les documents techniques sont ici.
> Pour la vision produit et les workflows → `GOAL.md` (racine)
> Pour les règles de dev permanent → `CLAUDE.md` (racine) · détail agent → [`CLAUDE-REFERENCE.md`](./CLAUDE-REFERENCE.md)

---

## Correspondance wiki (fichiers aplatis)

| Fichier sous `docs/` | Page sur le wiki (GitHub) |
|----------------------|---------------------------|
| `README.md` (ce fichier) | [Home](https://github.com/ldom1/clawvis/wiki) (`Home.md`) |
| `ARCHITECTURE.md` | `ARCHITECTURE` |
| `DATA-MODEL.md` | `DATA-MODEL` |
| `PITFALLS.md` | `PITFALLS` |
| `testing.md` | `testing` |
| `guides/deploy-hostinger.md` | `guides-deploy-hostinger` |
| `guides/dombot-edge-routing.md` | `guides-dombot-edge-routing` |
| `guides/openclaw-transcribe-channels.md` | `guides-openclaw-transcribe-channels` |
| `roadmap/v1.md` | `roadmap-v1` |
| `specs/2026-03-27-dombot-migration-design.md` | `specs-2026-03-27-dombot-migration-design` |
| `adr/README.md` | `adr-README` |
| `adr/0001-docker-as-default-mode.md` | `adr-0001-docker-as-default-mode` |
| `adr/0002-instance-scoped-memory.md` | `adr-0002-instance-scoped-memory` |
| `adr/0003-dombot-migration.md` | `adr-0003-dombot-migration` |
| `adr/0004-production-deployment-pitfalls.md` | `adr-0004-production-deployment-pitfalls` |
| `superpowers/plans/2026-03-21-clawvis-refactor.md` | `superpowers-plans-2026-03-21-clawvis-refactor` |
| `superpowers/plans/2026-03-23-oneliner-install.md` | `superpowers-plans-2026-03-23-oneliner-install` |

Liens wiki (syntaxe GitHub) : `[[guides-deploy-hostinger]]`, etc.

---

## Référence technique

| Document | Description |
|----------|-------------|
| [CLAUDE-REFERENCE.md](./CLAUDE-REFERENCE.md) | Complément de `CLAUDE.md` : modes, install détaillé, contrats étendus, CLI, GitNexus résumé |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Stack complète, API domains, routing SPA, Brain/Quartz, pattern Dombot edge, HUB_HOST |
| [DATA-MODEL.md](./DATA-MODEL.md) | États kanban, cycle de vie projet, paramètres configurables, schéma Brain PARA |
| [PITFALLS.md](./PITFALLS.md) | Bugs connus, dettes techniques, points de friction non résolus |
| [testing.md](./testing.md) | Inventaire exhaustif des tests — TLDR + détail par couche (Playwright, pytest, CI scripts) |

---

## Guides opérationnels

| Document | Description |
|----------|-------------|
| [guides/deploy-hostinger.md](./guides/deploy-hostinger.md) | Déploiement sur Hostinger VPS — Docker Manager hPanel + GitHub Actions |
| [guides/dombot-edge-routing.md](./guides/dombot-edge-routing.md) | Pattern Dombot : landing vs lab sur un seul port — nginx instance, Authelia, HUB_HOST |
| [guides/openclaw-transcribe-channels.md](./guides/openclaw-transcribe-channels.md) | OpenClaw + Telegram/Discord : transcription vocale via hub_core (Whisper local) |

---

## Roadmap

| Document | Description |
|----------|-------------|
| [roadmap/v1.md](./roadmap/v1.md) | Roadmap V1 — Phases 1 → 5, statuts, Definition of Done |

---

## Architecture Decision Records

| # | Titre | Statut |
|---|-------|--------|
| [0001](./adr/0001-docker-as-default-mode.md) | Docker comme mode d'install par défaut (Franc) | Accepted |
| [0002](./adr/0002-instance-scoped-memory.md) | Mémoire instance-scoped — jamais au root | Accepted |
| [0003](./adr/0003-dombot-migration.md) | Migration Dombot (Clawpilot → Clawvis) | Accepted |
| [0004](./adr/0004-production-deployment-pitfalls.md) | Pitfalls prod — premier déploiement Dombot | Accepted |

→ [Format et convention ADR](./adr/README.md)

---

## Specs

| Document | Description |
|----------|-------------|
| [specs/2026-03-27-dombot-migration-design.md](./specs/2026-03-27-dombot-migration-design.md) | Design spec Phase 1.5 — migration Dombot complète |

---

## Structure du dossier

```
docs/
  README.md               ← ce fichier
  CLAUDE-REFERENCE.md     ← complément règles agent (hors hot path)
  ARCHITECTURE.md         ← architecture technique fusionnée
  DATA-MODEL.md           ← modèle de données de référence
  PITFALLS.md             ← bugs connus et dettes
  testing.md              ← inventaire tests
  adr/
    README.md             ← index + format ADR
    0001-*.md → 0004-*.md
  guides/
    deploy-hostinger.md
    dombot-edge-routing.md
    openclaw-transcribe-channels.md
  roadmap/
    v1.md
  specs/
    2026-03-27-dombot-migration-design.md
```

---

## Fichiers supprimés / consolidés

| Ancien fichier | Remplacé par |
|----------------|--------------|
| `docs/architecture.md` (minuscule) | Fusionné dans `docs/ARCHITECTURE.md` |
| Checklist déploiement dans `roadmap/v1.md` | `docs/PITFALLS.md` + `docs/adr/0004` |