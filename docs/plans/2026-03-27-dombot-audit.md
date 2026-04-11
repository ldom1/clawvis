# Dombot Audit (Phase 1.5.1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produire `docs/adr/0003-dombot-migration.md` — snapshot complet de l'état actuel de Dombot (services, ports, nginx, skills, mémoire) avant toute migration.

**Architecture:** SSH vers devbox, collecte d'informations bash, rédaction du doc ADR. Aucune modification du serveur.

**Tech Stack:** bash, ssh devbox, markdown

---

### Task 1 : Inventaire des services et ports actifs

**Files:**
- Create: `docs/adr/0003-dombot-migration.md` (section Services)

- [ ] **Step 1 : Lister les processus qui écoutent sur un port**

```bash
ssh devbox "ss -tlnp | grep -v '127.0.0.1' | sort"
```

Expected : liste des ports ouverts (8088, 9091 authelia, etc.)

- [ ] **Step 2 : Lister les containers Docker actifs**

```bash
ssh devbox "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
```

- [ ] **Step 3 : Lister tous les containers (y compris arrêtés)**

```bash
ssh devbox "docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'"
```

- [ ] **Step 4 : Vérifier les services systemd actifs liés au lab**

```bash
ssh devbox "systemctl --user list-units --state=running 2>/dev/null; systemctl list-units --state=running 2>/dev/null | grep -E 'nginx|openclaw|clawvis|hub'"
```

---

### Task 2 : Audit nginx — routes et proxy_pass

**Files:**
- Create: `docs/adr/0003-dombot-migration.md` (section Nginx)

- [ ] **Step 1 : Capturer la config nginx générée complète**

```bash
ssh devbox "cat ~/Lab/hub-ldom/instances/ldom/logs/nginx-generated.conf"
```

- [ ] **Step 2 : Extraire la liste des routes avec leur destination**

```bash
ssh devbox "grep -E '^\s+(location|proxy_pass|root|alias)' ~/Lab/hub-ldom/instances/ldom/logs/nginx-generated.conf"
```

- [ ] **Step 3 : Vérifier la config nginx template (avant envsubst)**

```bash
ssh devbox "cat ~/Lab/hub-ldom/instances/ldom/nginx/nginx.conf | grep -E 'location|proxy_pass|server_name|listen|root|alias'"
```

- [ ] **Step 4 : Identifier les variables envsubst utilisées**

```bash
ssh devbox "grep -oE '\$\{[A-Z_]+\}' ~/Lab/hub-ldom/instances/ldom/nginx/nginx.conf | sort -u"
```

---

### Task 3 : Audit Authelia

**Files:**
- Create: `docs/adr/0003-dombot-migration.md` (section Authelia)

- [ ] **Step 1 : Lister les fichiers de config authelia**

```bash
ssh devbox "ls -la ~/Lab/hub-ldom/instances/ldom/authelia/"
```

- [ ] **Step 2 : Extraire la config principale (sans secrets)**

```bash
ssh devbox "cat ~/Lab/hub-ldom/instances/ldom/authelia/configuration.yml 2>/dev/null | grep -v -E 'secret|password|jwt|key' | head -60"
```

- [ ] **Step 3 : Lister les users/ACL (sans hash de mots de passe)**

```bash
ssh devbox "cat ~/Lab/hub-ldom/instances/ldom/authelia/users_database.yml 2>/dev/null | grep -v 'password'"
```

---

### Task 4 : Inventaire des skills

**Files:**
- Create: `docs/adr/0003-dombot-migration.md` (section Skills)

- [ ] **Step 1 : Lister les skills hub-ldom (privés)**

```bash
ssh devbox "ls -la ~/Lab/hub-ldom/instances/ldom/skills/"
```

- [ ] **Step 2 : Lister les skills OpenClaw (actuels)**

```bash
ssh devbox "ls -la ~/.openclaw/skills/ | awk '{print \$1, \$NF}'"
```

Expected : voir si ce sont des symlinks (`l`) ou des dossiers (`d`)

- [ ] **Step 3 : Lister les skills Clawvis core (publics)**

```bash
ls /home/lgiron/lab/clawvis/skills/
```

- [ ] **Step 4 : Construire la table de réconciliation**

Trois colonnes : `skill name | source actuelle (openclaw) | cible (public clawvis / privé ldom)`

Règle : un skill dans `clawvis/skills/` → public ; dans `hub-ldom/instances/ldom/skills/` → privé.

---

### Task 5 : Audit mémoire et workspace OpenClaw

**Files:**
- Create: `docs/adr/0003-dombot-migration.md` (section Mémoire)

- [ ] **Step 1 : Vérifier le symlink memory actuel**

```bash
ssh devbox "ls -la ~/.openclaw/workspace/memory"
```

Expected : `memory -> /home/lgiron/Lab/hub-ldom/instances/ldom/memory`

- [ ] **Step 2 : Lister la structure de la vault**

```bash
ssh devbox "find ~/.openclaw/workspace/memory -maxdepth 2 -type d | sort"
```

- [ ] **Step 3 : Vérifier l'état du workspace OpenClaw**

```bash
ssh devbox "ls -la ~/.openclaw/workspace/ && cat ~/.openclaw/workspace/MEMORY.md | head -20"
```

- [ ] **Step 4 : Vérifier openclaw.json (sans credentials)**

```bash
ssh devbox "cat ~/.openclaw/openclaw.json | python3 -c 'import json,sys; d=json.load(sys.stdin); [d.pop(k, None) for k in [\"auth\",\"credentials\"]]; print(json.dumps(d, indent=2))' | head -60"
```

---

### Task 6 : Audit variables d'environnement (sans secrets)

**Files:**
- Create: `docs/adr/0003-dombot-migration.md` (section Variables)

- [ ] **Step 1 : Lister les variables dans hub-ldom .env.local (sans valeurs sensibles)**

```bash
ssh devbox "cat ~/Lab/hub-ldom/instances/ldom/.env.local 2>/dev/null | grep -v -E 'KEY|SECRET|TOKEN|PASS|PWD|CREDENTIAL' | grep -v '^#' | grep -v '^$'"
```

- [ ] **Step 2 : Lister les variables dans clawvis .env**

```bash
ssh devbox "cat ~/Lab/clawvis/.env 2>/dev/null"
```

- [ ] **Step 3 : Identifier les variables nginx (HUB_ROOT, LAB, etc.)**

```bash
ssh devbox "grep -E 'HUB_ROOT|LAB|OPENCLAW|MEMORY' ~/Lab/hub-ldom/instances/ldom/scripts/*.sh 2>/dev/null | head -20"
```

---

### Task 7 : Rédiger docs/adr/0003-dombot-migration.md

**Files:**
- Create: `docs/adr/0003-dombot-migration.md`

- [ ] **Step 1 : Créer le fichier ADR avec toutes les infos collectées**

Structure du fichier :

```markdown
# ADR-0003 — Migration Dombot : Clawpilot → Clawvis

**Date :** 2026-03-27
**Statut :** En cours
**Contexte :** Snapshot pré-migration de l'état hub-ldom sur Dombot server

## 1. Services actifs (pré-migration)

| Service | Port | Image / Process | État |
|---------|------|-----------------|------|
| nginx (hub-ldom) | 8088 | nginx (user lgiron) | actif |
| authelia | 9091 | authelia/authelia:latest (Docker) | actif |
| ... | ... | ... | ... |

## 2. Routes nginx (lab.dombot.tech)

| Path | Destination | Auth |
|------|-------------|------|
| / | static landing | non |
| /memory/ | obsidian-remote | authelia |
| /brain-pulse/ | ... | authelia |
| ... | ... | ... |

## 3. Variables nginx (envsubst)

| Variable | Valeur actuelle |
|----------|----------------|
| HUB_ROOT | ~/Lab/hub-ldom/instances/ldom |
| LAB | ~/Lab |
| ... | ... |

## 4. Authelia

- Fichiers : configuration.yml, users_database.yml, ...
- Domaines protégés : lab.dombot.tech/*
- Utilisateurs : [liste sans hash]

## 5. Skills — table de réconciliation

| Skill | ~/.openclaw/skills | hub-ldom | clawvis/skills | Cible |
|-------|--------------------|----------|----------------|-------|
| brain-pulse | dossier réel | ✅ | ❌ | privé → ldom |
| logger | dossier réel | ❌ | ✅ | public → clawvis |
| ... | ... | ... | ... | ... |

## 6. Mémoire

- Symlink actuel : `~/.openclaw/workspace/memory → ~/Lab/hub-ldom/instances/ldom/memory`
- Structure vault : [résultat find]
- Cible migration : `~/.openclaw/workspace/memory → ~/Lab/clawvis/instances/ldom/memory`

## 7. Variables d'environnement non-sensibles

[résultat grep .env.local sans secrets]

## 8. Décisions de migration

- hub-ldom → déprécié après 1.5.3
- instances/ldom/ → créé par clawvis install (étape 1.5.2)
- docker-compose override → production réel (étape 1.5.5)
```

- [ ] **Step 2 : Commit**

```bash
git add docs/adr/0003-dombot-migration.md
git commit -m "update(docs): add ADR-0003 Dombot pre-migration snapshot"
```
