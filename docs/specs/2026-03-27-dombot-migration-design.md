# Design Spec — Phase 1.5 : Migration Dombot (Clawpilot → Clawvis)

**Date :** 2026-03-27
**Statut :** Approuvé — en attente d'implémentation
**Scope :** Déploiement production Clawvis sur Dombot server, remplacement de hub-ldom

---

## Contexte

Dombot est un serveur domestique personnel qui fait tourner une instance "Clawpilot" (hub-ldom) — l'ancienne architecture qui a précédé Clawvis. OpenClaw est installé sur ce serveur (`~/.openclaw/`) avec ses propres skills et une mémoire partagée via symlink.

L'objectif est de migrer vers Clawvis proprement, en validant le flow d'install et de déploiement production en conditions réelles.

### Architecture actuelle (avant migration)

```
~/Lab/hub-ldom/                  ← instance privée (dombot-lab-hub git repo)
  instances/ldom/
    nginx/                        ← nginx config (dombot.tech + lab.dombot.tech)
    authelia/                     ← SSO derrière lab.dombot.tech
    memory/                       ← vault mémoire ldom
    skills/                       ← 4 skills privés
    public/, scripts/, src/...

~/Lab/clawvis/                   ← core clawvis (public), NON actif
  instances/example/              ← template seulement

~/.openclaw/
  workspace/
    memory → hub-ldom/instances/ldom/memory/   ← symlink
  skills/                         ← 16 skills (mélange public/privé, vrais dossiers)
```

**Réseau :**
```
Internet → VPS OVH nginx (lab.dombot.tech) → Tailscale 100.64.162.103:8088
→ Dombot nginx (hub-ldom nginx) → services derrière Authelia
```

Aucun conteneur Clawvis Hub, kanban-api ou memory-api ne tourne actuellement.

---

## Philosophie cible

> **Clawvis = tour de contrôle d'OpenClaw.**
> Les skills et la mémoire ont une source de vérité unique dans Clawvis.
> OpenClaw pointe vers Clawvis, pas l'inverse.

---

## Architecture cible

### Arborescence

```
~/Lab/clawvis/
  skills/                             ← skills PUBLICS (core Clawvis, upstream)
    logger/
    kanban-implementer/
    git-sync/
    skill-tester/
    ...
  instances/
    ldom/                             ← créé par clawvis install, git = dombot-lab-hub
      docker-compose.override.yml     ← override production réel
      .env.local                      (gitignored — secrets)
      memory/                         ← vault ldom (source de vérité unique)
      nginx/nginx.conf                ← config nginx migrée de hub-ldom
      authelia/                       ← config authelia migrée
      skills/                         ← skills PRIVÉS ldom
        brain-pulse/
        dombot-mail/
        hub-refresh/
        system-restart/
      public/
      scripts/

~/Lab/hub-ldom/                      ← DÉPRÉCIÉ, archivé après migration

~/.openclaw/
  workspace/
    memory → ~/Lab/clawvis/instances/ldom/memory/  ← symlink mis à jour
  skills/
    # Skills publics → symlinks vers clawvis/skills/
    logger        → ~/Lab/clawvis/skills/logger/
    kanban-*      → ~/Lab/clawvis/skills/kanban-*/
    git-sync      → ~/Lab/clawvis/skills/git-sync/
    skill-tester  → ~/Lab/clawvis/skills/skill-tester/
    brain-maintenance → ~/Lab/clawvis/skills/brain-maintenance/
    knowledge-consolidator → ~/Lab/clawvis/skills/knowledge-consolidator/
    morning-briefing → ~/Lab/clawvis/skills/morning-briefing/
    proactive-innovation → ~/Lab/clawvis/skills/proactive-innovation/
    qmd           → ~/Lab/clawvis/skills/qmd/
    reverse-prompt → ~/Lab/clawvis/skills/reverse-prompt/
    ruflo         → ~/Lab/clawvis/skills/ruflo/
    self-improvement → ~/Lab/clawvis/skills/self-improvement/
    # Skills privés → symlinks vers instances/ldom/skills/
    brain-pulse   → ~/Lab/clawvis/instances/ldom/skills/brain-pulse/
    dombot-mail   → ~/Lab/clawvis/instances/ldom/skills/dombot-mail/
    hub-refresh   → ~/Lab/clawvis/instances/ldom/skills/hub-refresh/
    system-restart → ~/Lab/clawvis/instances/ldom/skills/system-restart/
```

### Flux réseau cible

```
Internet
  → VPS OVH nginx (lab.dombot.tech, IP fixe)
    → proxy_pass Tailscale 100.64.162.103:8088
      → Dombot nginx (instances/ldom/nginx/)   [port 8088]
          /              → Clawvis Hub SPA (conteneur hub)
          /api/hub/*     → kanban-api + hub-memory-api
          /memory/       → Obsidian remote (conservé)
          /brain-pulse/  → service brain-pulse (conservé)
          /authelia/     → Authelia (conservé)
          /plume/, /real-estate/, /debate/, /poems/, /techspend/  (conservés)
```

### docker-compose production

```bash
# Commande de déploiement production
docker compose \
  -f ~/Lab/clawvis/docker-compose.yml \
  -f ~/Lab/clawvis/instances/ldom/docker-compose.override.yml \
  up -d
```

Le `docker-compose.override.yml` de ldom définit :
- Ports réels (`HUB_PORT=8088`, `KANBAN_API_PORT=8090`, `HUB_MEMORY_API_PORT=8091`)
- Volumes : nginx config, authelia, memory vault
- Services additionnels : kanban-api, hub-memory-api, authelia, nginx
- Réseaux : bridge nginx avec les services existants (brain-pulse, plume, etc.)

---

## Auto-symlink des nouveaux skills

### Principe

Quand un nouveau skill est créé (dans `clawvis/skills/` ou `instances/ldom/skills/`), il doit être automatiquement disponible dans OpenClaw sans intervention manuelle.

### Commande

```bash
clawvis skills sync
```

Comportement :
1. Scanne `~/Lab/clawvis/skills/*/` → crée symlinks publics dans `~/.openclaw/skills/`
2. Scanne `~/Lab/clawvis/instances/ldom/skills/*/` → crée symlinks privés
3. Si `~/.openclaw/skills/<name>` est un vrai dossier (ancienne install) → `WARN: manual dir found, skipping`
4. Ne supprime jamais de symlinks existants (ajout seulement)

### Git hooks

`.githooks/post-merge` dans `clawvis/` et dans `instances/ldom/` (dombot-lab-hub) :
```bash
#!/bin/bash
# Auto-sync skills symlinks après git pull
clawvis skills sync
```

Installation : `git config core.hooksPath .githooks` (déjà en place pour commit-msg).

---

## Étapes de la phase 1.5

### 1.5.1 — Audit & snapshot de hub-ldom

- Documenter tous les services actifs, ports, variables d'env (sans secrets)
- Sauvegarder la config nginx générée
- Inventaire des skills : lequel est dans hub-ldom vs ~/.openclaw uniquement
- Livrable : `docs/adr/0003-dombot-migration.md`

### 1.5.2 — `clawvis install` sur Dombot

- Lancer le wizard Clawvis avec `INSTANCE_NAME=ldom` sur le serveur
- Valider que la structure `instances/ldom/` est créée correctement (test réel du flow)
- Initialiser `instances/ldom/` comme repo git avec remote `dombot-lab-hub`
- Premier commit : structure template standard

### 1.5.3 — Migration hub-ldom → instances/ldom/

Contenu à migrer :
- `nginx/nginx.conf` → adapter les proxy_pass pour pointer vers les conteneurs Clawvis
- `authelia/` → copie directe
- `memory/` → conserver en place (déjà à la bonne structure)
- `skills/` (4 skills privés) → copier dans `instances/ldom/skills/`
- `docker-compose.override.yml` → réécrire pour production réelle Clawvis
- `.env.local` → migrer les variables (sans secrets trackés)

### 1.5.4 — Symlinks OpenClaw

Mettre à jour `~/.openclaw/workspace/memory` :
```bash
rm ~/.openclaw/workspace/memory
ln -s ~/Lab/clawvis/instances/ldom/memory ~/.openclaw/workspace/memory
```

Vider les anciens dossiers skills et créer les symlinks :
```bash
clawvis skills sync  # premier run manuel
```

Installer le git hook post-merge sur les deux repos.

### 1.5.5 — Déploiement production

```bash
cd ~/Lab/clawvis
docker compose \
  -f docker-compose.yml \
  -f instances/ldom/docker-compose.override.yml \
  up -d
```

Validation :
- `curl http://localhost:8088/` → Hub SPA répond
- `curl http://localhost:8090/api/kanban/projects` → kanban-api répond
- `curl http://localhost:8091/api/hub/memory/tree` → memory-api répond
- `lab.dombot.tech/` → Clawvis Hub accessible depuis le navigateur via VPS

### 1.5.6 — Validation OpenClaw branché

- Hub Settings → AI Runtime → sélectionner OpenClaw, URL `http://localhost:3333`
- `GET /api/hub/chat/status` → `{"openclaw_configured": true}`
- Envoyer un message depuis `/chat/` → réponse reçue
- Vérifier que les skills OpenClaw sont bien chargés depuis les symlinks

---

## Critères de sortie

- [ ] `clawvis install` a créé `instances/ldom/` proprement (flow validé en conditions réelles)
- [ ] `hub-ldom` est déprécié et archivé
- [ ] `~/.openclaw/skills/*` = 100% symlinks (aucun vrai dossier)
- [ ] `~/.openclaw/workspace/memory` → `clawvis/instances/ldom/memory/`
- [ ] `clawvis skills sync` fonctionne et les nouveaux skills sont auto-symlinkés
- [ ] `docker compose -f ... -f instances/ldom/docker-compose.override.yml up` déploie tout
- [ ] `lab.dombot.tech/` affiche Clawvis Hub SPA
- [ ] Authelia toujours fonctionnel sur `lab.dombot.tech`
- [ ] Services existants (memory, brain-pulse, etc.) toujours accessibles
- [ ] OpenClaw répond via Hub Chat

---

## Décisions d'architecture

**ADR-0003 :** `instances/ldom/` dans `clawvis/` (Option B) — clone de dombot-lab-hub posé manuellement, gitignored par clawvis core, `upstream=clawvis` conservé dans dombot-lab-hub pour les éventuels `git fetch upstream`.

**Pourquoi pas submodule :** La gestion des submodules en prod est fragile (init/update oubliés). L'instance est gitignored et gérée indépendamment, ce qui correspond au contrat Clawvis.

**Pourquoi recréer via `clawvis install` :** Valide le flow d'install en conditions réelles. C'est un test de bout en bout de la Phase 1 sur une vraie machine.
