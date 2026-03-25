# Clawvis V1 — Roadmap de lancement

> Objectif : Clawvis en production avec OpenClaw connecté (local + Hostinger), installable en 1 commande, prêt à être annoncé.

---

## Phase 1 — Fondations stables

**Critère de sortie :** `bash tests/ci-all.sh` passe, l'install en mode Franc fonctionne de bout en bout.

| # | Action | Fichier(s) concerné(s) | Statut |
|---|--------|------------------------|--------|
| 1.1 | Rendre le dépôt public sur GitHub | Paramètres GitHub | [ ] |
| 1.2 | Vérifier `get.sh` : clone dans `~/.clawvis`, symlink `clawvis`, PATH injection | `get.sh`, `install.sh` | [ ] |
| 1.3 | Smoke test install Franc end-to-end (Docker compose up, Hub charge, Kanban charge) | `docker-compose.yml`, `hub/nginx.conf` | [ ] |
| 1.4 | CI verte sur `main` (shell, format, build, Python, Playwright skip-only) | `.github/workflows/ci.yml` | [ ] |
| 1.5 | `hub/public/settings/index.html` — vérifier parité avec SPA (prefixes API corrects) | `hub/public/settings/index.html` | [x] |
| 1.6 | Kanban API + Memory API inclus dans docker-compose avec proxy nginx correct | `docker-compose.yml`, `hub/nginx.conf` | [x] |

---

## Phase 2 — Connexion OpenClaw

**Critère de sortie :** le Chat Hub envoie un message et reçoit une réponse d'OpenClaw (local ou Hostinger).

### 2A — OpenClaw local (dev)

| # | Action | Détails |
|---|--------|---------|
| 2A.1 | Démarrer une instance OpenClaw en local | `docker run` ou `uvicorn` sur port 11434/8080 selon la distrib |
| 2A.2 | Dans `/settings/` → AI Runtime : sélectionner **OpenClaw**, saisir l'URL locale | `http://localhost:<port>` |
| 2A.3 | Tester la connexion depuis le wizard → doit retourner `{"status": "ok"}` | `GET /api/hub/chat/status` |
| 2A.4 | Envoyer un message depuis `/chat/` → vérifier la réponse streaming | `POST /api/hub/chat/` |
| 2A.5 | Activer le service `openclaw` dans `docker-compose.yml` (retirer le commentaire) | `docker-compose.yml` ligne ~81 |

### 2B — OpenClaw Hostinger (prod)

| # | Action | Détails |
|---|--------|---------|
| 2B.1 | Déployer OpenClaw sur Hostinger (VPS ou conteneur) | URL cible : `https://openclaw.<domaine>` |
| 2B.2 | Configurer CORS sur OpenClaw pour autoriser le domaine Hub | Config OpenClaw |
| 2B.3 | Dans `/settings/` Hub prod : saisir l'URL Hostinger + API key | Stocké dans `localStorage` (frontend) ou `.env` (backend) |
| 2B.4 | Test de connexion + envoi d'un message depuis le Hub prod | Même flow que 2A.3/2A.4 |
| 2B.5 | Ajouter `OPENCLAW_BASE_URL` et `OPENCLAW_API_KEY` dans `.env.example` | `.env.example` |

### 2C — Test E2E Chat

| # | Action | Détails |
|---|--------|---------|
| 2C.1 | Étendre `tests/personas/chat.spec.ts` : quand backend key configuré, vérifier bulle assistant non vide | `tests/playwright/tests/personas/chat.spec.ts` |
| 2C.2 | Ajouter la variable `CLAWVIS_OPENCLAW_URL` dans `tests/ci-playwright.sh` pour CI avec vrai provider | `tests/ci-playwright.sh` |

---

## Phase 3 — Onboarding V1

**Critère de sortie :** un développeur qui n'a jamais vu Clawvis peut démarrer en < 5 minutes.

| # | Action | Fichier(s) concerné(s) |
|---|--------|------------------------|
| 3.1 | README : mettre `get.sh` one-liner EN PREMIER, avant tout | `README.md` |
| 3.2 | README : section "Démarrage rapide" avec captures d'écran Hub + Chat | `README.md`, `docs/screenshots/` |
| 3.3 | README : section "Connecter OpenClaw" pointant vers `/settings/` | `README.md` |
| 3.4 | Commande `clawvis setup provider` (CLI post-install) | `clawvis-cli/` |
| 3.5 | Fresh install smoke test sur machine propre (VM ou container) | — |
| 3.6 | Vérifier que le wizard `/setup/runtime/` guide correctement vers OpenClaw | `hub/src/main.js` |
| 3.7 | Ajouter `OPENCLAW_BASE_URL` dans le wizard comme valeur d'exemple | `hub/src/main.js` |

---

## Phase 4 — Lancement

**Critère de sortie :** tag de release publié, annonce prête.

| # | Action | Détails |
|---|--------|---------|
| 4.1 | Tag `v2026-03-25` (ou date de release) | `git tag v2026-03-25 && git push origin v2026-03-25` |
| 4.2 | GitHub Release auto-générée via `release.yml` | `.github/workflows/release.yml` |
| 4.3 | Vérifier que `get.sh` pointe sur le bon tag/branch | `get.sh` |
| 4.4 | Captures d'écran pour l'annonce : Hub home, Kanban, Brain, Chat | `docs/screenshots/` |
| 4.5 | Annonce : X/Twitter, LinkedIn, Reddit r/selfhosted — mettre le one-liner en avant | — |
| 4.6 | Post-lancement : surveiller les issues GitHub (onboarding feedback) | GitHub Issues |

---

## Dépendances critiques

```
Phase 1 ──► Phase 2A (local) ──► Phase 2C (E2E Chat)
                 │
                 └──► Phase 2B (Hostinger) ──► Phase 3 ──► Phase 4
```

Phase 1 doit être complète avant de brancher OpenClaw en production. La Phase 3 peut commencer en parallèle de la Phase 2B.

---

## Définition of Done — V1

- [ ] `get.sh | bash` fonctionne sur une machine propre (Ubuntu 22+, macOS 14+)
- [ ] Hub charge en < 3 secondes (mode Franc, Docker local)
- [ ] Chat répond via OpenClaw (local ou Hostinger)
- [ ] Kanban : créer une tâche, la bouger, l'archiver
- [ ] Brain : Quartz iframe charge, fichier `.md` modifiable
- [ ] Settings : provider configuré, connexion testée
- [ ] CI verte sur `main`
- [ ] README lisible par un non-développeur

---

## Stack de référence V1

| Composant | Technologie | Mode Franc | Mode Mérovingien |
|-----------|-------------|------------|------------------|
| Hub SPA | Vite + vanilla JS | Docker (nginx) | nginx VPS |
| Kanban API | FastAPI / uvicorn | Docker | systemd / Docker |
| Memory API | FastAPI / uvicorn | Docker | systemd / Docker |
| Brain display | Quartz static (iframe) | build one-shot | build CI |
| OpenClaw | LLM runtime | Local Docker | Hostinger VPS |
| Base de données | Fichiers Markdown | `instances/<name>/memory/` | même structure |
