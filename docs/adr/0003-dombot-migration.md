# ADR-0003 — Migration Dombot : Clawpilot → Clawvis

**Date :** 2026-03-27
**Statut :** Pré-migration snapshot (historique) — pour le routage public actuel (**`lab.dombot.tech`** vs landing **`clawvis.fr`**) et **`HUB_HOST`**, voir **[guides/dombot-edge-routing.md](../guides/dombot-edge-routing.md)**.
**Auteur :** audit automatisé Phase 1.5.1

## Contexte

Le serveur Dombot (`lab.dombot.tech`) fait tourner `hub-ldom`, une instance Clawpilot (ancien nom) avec nginx, Authelia, et plusieurs APIs Python. L'objectif est de migrer cette instance vers `clawvis/instances/ldom/` pour bénéficier du cycle de mise à jour Clawvis en conservant toutes les routes, credentials et données mémoire existants. Ce document capture l'état exact du système avant toute modification.

## 1. Services actifs (pré-migration)

| Port | Bind | Process / Image | État | Rôle |
|------|------|-----------------|------|------|
| 8088 | 0.0.0.0 | nginx (user lgiron) | actif | Hub ldom (hub-ldom nginx) |
| 9091 | 127.0.0.1 | authelia/authelia:latest (Docker) | Up 4 days (healthy) | Auth gateway |
| 18789 | 127.0.0.1 + ::1 | openclaw-gateway (systemd user) | active running | OpenClaw Gateway v2026.3.11 |
| 18791 | 127.0.0.1 | openclaw-gateway | active running | idem (worker) |
| 18792 | 127.0.0.1 | openclaw-gateway | active running | idem (worker) |
| 8090 | 127.0.0.1 | python3 uvicorn | actif | kanban_api |
| 8000 | 127.0.0.1 | python3 | actif | optimizer_api |
| 8092 | 127.0.0.1 | python | actif | spendlens_api |
| 8501 | 127.0.0.1 | python3 | actif | messidor |
| 5175 | 0.0.0.0 | node (Vite dev server) | actif | brain-pulse (probable) |
| 3010 | * | next-server | actif | debate app |
| 16152 | 0.0.0.0 | Tailscale | actif | réseau privé |
| 80 | 0.0.0.0 | nginx système (root) | actif | entrypoint HTTP |

**Seul container Docker actif :** `lab-authelia` (authelia/authelia:latest).

**Systemd user service notable :** `openclaw-gateway.service` — loaded active running, OpenClaw Gateway v2026.3.11.

## 2. Routes nginx

### dombot.tech (public, sans authentification)

| Path | Type | Destination |
|------|------|-------------|
| `/` | static | `~/Lab/clawvis-landing/dist` |
| `/assets/` | static | `~/Lab/clawvis-landing/dist` |
| `/docs/` | static | `~/Lab/clawvis-landing/dist` |

### lab.dombot.tech (derrière Authelia)

| Path | Type | Destination | Notes migration |
|------|------|-------------|-----------------|
| `/` | static | `hub-ldom/instances/ldom/public/` | → `clawvis/instances/ldom/public/` |
| `/memory/` | static | `/home/lgiron/Lab/quartz/public/` | Quartz Brain build — inchangé |
| `/brain-pulse/` | static | `~/Lab/project/brain-pulse/dist/` | projet séparé |
| `/plume/` | static | `hub-ldom/instances/ldom/public/plume/` | → `clawvis/instances/ldom/public/plume/` |
| `/real-estate/` | static | `~/Lab/project/real-estate/frontend/` | projet séparé |
| `/debate/` | proxy | `debate_api` → 127.0.0.1:3010 (Next.js) | service indépendant |
| `/poems/` | static | `~/Lab/poc/vitrine-poeme/dist/` | projet séparé |
| `/techspend/` | static + proxy | `spendlens_api` → 127.0.0.1:8092 pour `/api/` | service indépendant |
| `/optimizer/` | static | `hub-ldom/instances/ldom/public/optimizer/` | → `clawvis/instances/ldom/public/optimizer/` |
| `/greet/` | static | `hub-ldom/instances/ldom/public/greet/` | → `clawvis/instances/ldom/public/greet/` |
| `/adele-icecream/` | static | `hub-ldom/instances/ldom/public/adele-icecream/` | → `clawvis/instances/ldom/public/adele-icecream/` |
| `/kanban/` | static | `hub-ldom/instances/ldom/public/kanban/` | ancien Kanban static → remplacé par Hub SPA |
| `/logs/` | static | `clawvis/core-tools/logger/` | déjà Clawvis ✅ |
| `/settings/` | static | `hub-ldom/instances/ldom/public/settings/` | ancien Settings static → remplacé par Hub SPA |
| `/tutti-frottie/` | static | `~/Lab/poc/tutti-frottie/` | projet séparé |
| `/openclaw/` | proxy | `openclaw` → 127.0.0.1:18789 | gateway token requis |
| `/api/kanban/` | proxy | `kanban_api` → 127.0.0.1:8090 | → même port post-migration |
| `/api/` | proxy | `debate_api` → 127.0.0.1:3010 | service indépendant |
| `/optimizer/api/` | proxy | `optimizer_api` → 127.0.0.1:8000 | service indépendant |
| `/messidor/` | proxy | `messidor` → 127.0.0.1:8501 | service indépendant |
| `/poetic-shield/` | proxy | `poetic_shield` → 127.0.0.1:8503 | service indépendant |
| `/api/tokens.json` | static (auth) | `hub-ldom/instances/ldom/public/api/tokens.json` | → `clawvis/instances/ldom/public/api/` |
| `/api/system.json` | static (auth) | `hub-ldom/instances/ldom/public/api/system.json` | idem |
| `/api/providers.json` | static (auth) | idem | idem |
| `/api/status.json` | static (auth) | idem | idem |
| `/authelia/` | proxy | authelia Docker → 127.0.0.1:9091 | inchangé |

**Upstreams nginx définis :**

```nginx
upstream debate_api    { server 127.0.0.1:3010; }
upstream optimizer_api { server 127.0.0.1:8000; }
upstream messidor      { server 127.0.0.1:8501; }
upstream poetic_shield { server 127.0.0.1:8503; }
upstream kanban_api    { server 127.0.0.1:8090; }
upstream spendlens_api { server 127.0.0.1:8092; }
upstream authelia      { server 127.0.0.1:9091; }
upstream openclaw      { server 127.0.0.1:18789; }
```

## 3. Variables nginx (envsubst)

| Variable | Résolution actuelle | Calcul |
|----------|---------------------|--------|
| `${HUB_ROOT}` | `~/Lab/hub-ldom/instances/ldom` | calculé dans `nginx-reload.sh` |
| `${LAB}` | `~/Lab` | 4× dirname depuis `scripts/` |
| `${OPENCLAW_GATEWAY_TOKEN}` | depuis `~/.openclaw/.env` ou `openclaw.json .gateway.auth.token` | secret — ne pas versionner |

**Piège critique — variable `LAB` :** `LAB` est calculé en remontant 4 niveaux de `dirname` depuis `scripts/` (scripts → ldom → instances → hub-ldom → Lab). Si le calcul utilise seulement 3× dirname, `LAB` vaut `hub-ldom/` et **toutes les routes static servent des 404 silencieux**. Vérifier ce calcul après toute modification de l'arborescence.

## 4. Authelia

| Paramètre | Valeur |
|-----------|--------|
| Config | `hub-ldom/instances/ldom/authelia/configuration.yml` |
| Users | `hub-ldom/instances/ldom/authelia/users_database.yml` |
| Domain | `dombot.tech` |
| Session expiration | 12h, inactivité 45min |
| Auth method | two_factor (TOTP, issuer: dombot.tech) |
| Storage | SQLite (`/config/data/db.sqlite3` dans le container) |
| Utilisateur | `ldom` (email: ldom@dombot.tech, group: admins) |
| Fichiers container | `/config/` |

**Post-migration :** les fichiers de config Authelia devront être déplacés vers `clawvis/instances/ldom/authelia/` et le volume Docker mis à jour en conséquence.

## 5. Skills — état actuel et cible migration

**Note :** les skills sont déjà partiellement migrés (symlinks). Les 12 skills core pointent déjà vers `clawvis/skills/`. Seuls 4 skills privés pointent encore vers `hub-ldom`.

| Skill | État actuel | Pointe vers (actuel) | Cible post-migration |
|-------|-------------|----------------------|----------------------|
| brain-maintenance | symlink ✅ | `~/Lab/clawvis/skills/brain-maintenance` | inchangé |
| git-sync | symlink ✅ | `~/Lab/clawvis/skills/git-sync` | inchangé |
| kanban-implementer | symlink ✅ | `~/Lab/clawvis/skills/kanban-implementer` | inchangé |
| knowledge-consolidator | symlink ✅ | `~/Lab/clawvis/skills/knowledge-consolidator` | inchangé |
| logger | symlink ✅ | `~/Lab/clawvis/skills/logger` | inchangé |
| morning-briefing | symlink ✅ | `~/Lab/clawvis/skills/morning-briefing` | inchangé |
| proactive-innovation | symlink ✅ | `~/Lab/clawvis/skills/proactive-innovation` | inchangé |
| qmd | symlink ✅ | `~/Lab/clawvis/skills/qmd` | inchangé |
| reverse-prompt | symlink ✅ | `~/Lab/clawvis/skills/reverse-prompt` | inchangé |
| ruflo | symlink ✅ | `~/Lab/clawvis/skills/ruflo` | inchangé |
| self-improvement | symlink ✅ | `~/Lab/clawvis/skills/self-improvement` | inchangé |
| skill-tester | symlink ✅ | `~/Lab/clawvis/skills/skill-tester` | inchangé |
| brain-pulse | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/brain-pulse` | `clawvis/instances/ldom/skills/brain-pulse` |
| dombot-mail | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/dombot-mail` | `clawvis/instances/ldom/skills/dombot-mail` |
| hub-refresh | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/hub-refresh` | `clawvis/instances/ldom/skills/hub-refresh` |
| system-restart | symlink ⚠️ | `~/Lab/hub-ldom/instances/ldom/skills/system-restart` | `clawvis/instances/ldom/skills/system-restart` |

**Action requise :** copier les 4 skills privés (`brain-pulse`, `dombot-mail`, `hub-refresh`, `system-restart`) vers `clawvis/instances/ldom/skills/`, puis mettre à jour les 4 symlinks.

## 6. Mémoire

**Symlink actuel :**
```
~/.openclaw/workspace/memory -> /home/lgiron/Lab/hub-ldom/instances/ldom/memory
```

**Structure de la vault (inchangée après migration) :**
```
memory/
  archive/
  breadcrumbs.md
  caps/
  consolidation/
  daily/
  DomBot-brain.md
  index.md
  kanban/
  projects/
  resources/
  todo/
```

**Post-migration :** mettre à jour le symlink pour pointer vers `~/Lab/clawvis/instances/ldom/memory`. La structure interne reste identique (move, pas copy).

## 7. Scripts hub-ldom

Scripts présents dans `hub-ldom/instances/ldom/scripts/` :

| Script | Rôle présumé |
|--------|--------------|
| `healthcheck.sh` | Vérification santé des services |
| `hub_update_loop.sh` | Boucle de mise à jour du Hub (polling) |
| `nginx-reload.sh` | Recalcul des variables envsubst + reload nginx |
| `restart.sh` | Redémarrage de la stack |
| `session-end-tracker.sh` | Tracking fin de session OpenClaw |
| `start.sh` | Démarrage de la stack |
| `stop.sh` | Arrêt de la stack |
| `system_audit.sh` | Audit système (génère system.json ou équivalent) |
| `transcribe-audio.sh` | Transcription audio (service ponctuel) |
| `update-projects-and-reload.sh` | Mise à jour projets + reload nginx |

**Post-migration :** ces scripts devront être copiés ou portés vers `clawvis/instances/ldom/scripts/`. Les chemins hardcodés vers `hub-ldom/` devront être mis à jour.

## 8. OpenClaw config

| Paramètre | Valeur |
|-----------|--------|
| Version | 2026.3.11 |
| Agent primary model | `anthropic/claude-haiku-4-5` |
| Subagents model | `mistral/mistral-small-3.2-24b-instruct` (via MammouthAI `https://api.mammouth.ai/v1`) |
| Max concurrent subagents | 8 |
| Workspace | `~/.openclaw/workspace` |
| Config | `openclaw.json` (credentials exclus de ce document) |

## 9. Décisions de migration

La migration se déroule en étapes Phase 1.5.x :

| Phase | Action | Impact |
|-------|--------|--------|
| 1.5.1 | Audit complet de l'état pré-migration (ce document) | Aucun — lecture seule |
| 1.5.2 | Copier `instances/ldom/` de hub-ldom vers `clawvis/instances/ldom/` | Crée la cible sans casser l'existant |
| 1.5.3 | Mettre à jour les 4 symlinks skills privés | Skills privés pointent vers clawvis |
| 1.5.4 | Mettre à jour le symlink mémoire | Mémoire pointe vers clawvis |
| 1.5.5 | Mettre à jour `nginx-reload.sh` + variable `HUB_ROOT` | nginx sert depuis clawvis |
| 1.5.6 | Smoke test complet + désactivation hub-ldom | Migration validée |

## 10. Points d'attention

- **Piège variable `LAB` (4× dirname) :** Si l'arborescence change ou si `nginx-reload.sh` est porté sans adapter le calcul, toutes les routes static servent 404. Toujours vérifier `echo $LAB` après modification.
- **`OPENCLAW_GATEWAY_TOKEN` :** Le token est lu depuis `~/.openclaw/.env` ou `openclaw.json`. Il ne doit jamais être versionné. S'assurer que `.env.local` dans `clawvis/instances/ldom/` est bien dans `.gitignore`.
- **Authelia volumes Docker :** Le container monte `/config/` en volume. Lors du déplacement des fichiers de config, recréer le container (`docker rm lab-authelia`) pour que le nouveau chemin soit pris en compte.
- **4 symlinks skills privés à mettre à jour :** `brain-pulse`, `dombot-mail`, `hub-refresh`, `system-restart` — encore sur hub-ldom, à migrer manuellement.
- **`HUB_PORT=5678` dans `clawvis/.env` :** Variable vestige de l'ancien nom (Clawpilot). Non utilisée en production. Supprimer ou corriger pour éviter toute confusion avec le port réel 8088.
- **`/kanban/` et `/settings/` routes statiques :** Ces routes servent l'ancien Kanban et Settings statiques. Après migration Hub SPA, ces routes devront être remplacées ou redirectées vers le Hub principal (`/`).
- **`poetic_shield` sur port 8503 :** Défini dans les upstreams nginx mais non listé dans `ss -tlnp` → service probablement arrêté ou intermittent. Vérifier avant de migrer la config nginx.
- **brain-pulse Vite dev server (port 5175) :** Tourne en mode dev (`node`). Vérifier s'il doit être buildé en static ou maintenu comme proxy en production.
