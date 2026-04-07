# Clawvis — Documentation

**Clawvis** is a self-hosted agent control hub: Kanban, Brain (memory / Quartz), AI runtime, logs — stack documented in this folder.

**Source repository**: [github.com/ldom1/clawvis](https://github.com/ldom1/clawvis).

> **GitHub wiki (mirror)** — This documentation is [automatically synced](https://github.com/ldom1/clawvis/actions/workflows/sync-wiki.yml) from `docs/` to the [wiki](https://github.com/ldom1/clawvis/wiki). **Do not edit the wiki directly**: all changes go through the Markdown files in [`docs/`](https://github.com/ldom1/clawvis/tree/main/docs) on the main repo. Content is **flattened** to the wiki root (no subfolders); relative links from the repo work locally / on GitHub, not always in the wiki UI — see [Wiki mapping](#wiki-mapping-flattened-files). If the workflow cannot push to the wiki, add a repo secret `WIKI_SYNC_TOKEN` (PAT with `repo` scope).

> Navigation index. All technical documents are here.
> For product vision and workflows → `docs/GOAL.md` (repo root)
> For permanent dev rules → `CLAUDE.md` (repo root) · agent detail → [`CLAUDE-REFERENCE.md`](./CLAUDE-REFERENCE.md)

---

## Wiki mapping (flattened files)

| File under `docs/` | Wiki page (GitHub) |
|--------------------|--------------------|
| `README.md` (this file) | [Home](https://github.com/ldom1/clawvis/wiki) (`Home.md`) |
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

Wiki links (GitHub syntax): `[[guides-deploy-hostinger]]`, etc.

---

## Technical reference

| Document | Description |
|----------|-------------|
| [CLAUDE-REFERENCE.md](./CLAUDE-REFERENCE.md) | Complement to `CLAUDE.md`: modes, detailed install, extended contracts, CLI, GitNexus summary |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Full stack, API domains, SPA routing, Brain/Quartz, Dombot edge pattern, HUB_HOST |
| [DATA-MODEL.md](./DATA-MODEL.md) | Kanban states, project lifecycle, configurable parameters, Brain PARA schema |
| [PITFALLS.md](./PITFALLS.md) | Known bugs, technical debt, unresolved friction |
| [testing.md](./testing.md) | Full test inventory — TLDR + detail per layer (Playwright, pytest, CI scripts) |

---

## Operational guides

| Document | Description |
|----------|-------------|
| [guides/deploy-hostinger.md](./guides/deploy-hostinger.md) | Deploy on Hostinger VPS — Docker Manager hPanel + GitHub Actions |
| [guides/dombot-edge-routing.md](./guides/dombot-edge-routing.md) | Dombot pattern: landing vs lab on one port — instance nginx, Authelia, HUB_HOST |
| [guides/openclaw-transcribe-channels.md](./guides/openclaw-transcribe-channels.md) | OpenClaw + Telegram/Discord: voice transcription via hub_core (local Whisper) |

---

## Roadmap

| Document | Description |
|----------|-------------|
| [roadmap/v1.md](./roadmap/v1.md) | V1 roadmap — Phases 1 → 5, status, Definition of Done |

---

## Architecture Decision Records

| # | Title | Status |
|---|-------|--------|
| [0001](./adr/0001-docker-as-default-mode.md) | Docker as default install mode (Franc) | Accepted |
| [0002](./adr/0002-instance-scoped-memory.md) | Instance-scoped memory — never at repo root | Accepted |
| [0003](./adr/0003-dombot-migration.md) | Dombot migration (Clawpilot → Clawvis) | Accepted |
| [0004](./adr/0004-production-deployment-pitfalls.md) | Production pitfalls — first Dombot deploy | Accepted |

→ [ADR format and convention](./adr/README.md)

---

## Specs

| Document | Description |
|----------|-------------|
| [specs/2026-03-27-dombot-migration-design.md](./specs/2026-03-27-dombot-migration-design.md) | Phase 1.5 design spec — full Dombot migration |

---

## Folder structure

```
docs/
  README.md               ← this file
  CLAUDE-REFERENCE.md     ← agent rules complement (off hot path)
  ARCHITECTURE.md         ← merged technical architecture
  DATA-MODEL.md           ← reference data model
  PITFALLS.md             ← known bugs and debt
  testing.md              ← test inventory
  adr/
    README.md             ← index + ADR format
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

## Removed / consolidated files

| Old file | Replaced by |
|----------|-------------|
| `docs/architecture.md` (lowercase) | Merged into `docs/ARCHITECTURE.md` |
| Deployment checklist in `roadmap/v1.md` | `docs/PITFALLS.md` + `docs/adr/0004` |
