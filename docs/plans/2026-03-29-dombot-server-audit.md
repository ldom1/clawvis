# Audit serveur Dombot (ssh devbox) — 2026-03-29

Environnement vérifié : `lgiron-home-debian`, dépôt Clawvis à `/home/lgiron/Lab/clawvis` (pas `~/lab/clawvis`).

---

## 1. Cartographie roadmap (Local Brain + dépôt)

### Source Local Brain (`clawvis.md`)

| Zone | État noté |
|------|-----------|
| Phase 1 | Terminée |
| Phase 1.5 (migration Dombot) | Terminée |
| Phase 2A | Quasi complète — **2A.7** `clawvis skills sync` / skills chat : ouvert |
| Phase 2.5 laptop-first | Non démarrée (priorité produit) |
| 2B Hostinger / 2C E2E / Phase 3+ | Non démarrées |

### `docs/roadmap/v1.md` (repo)

- Phase 2A.6 (validation navigateur `lab.dombot.tech/hub/...`) encore **[ ]** dans le tableau.
- Alignement : le cœur “OpenClaw + agent + settings API” est vert côté spec ; il reste friction **UI / routes / ops** (voir §3–4).

### Observations machine (devbox)

- Stack Docker : `clawvis-hub-1` → `127.0.0.1:8089`, `kanban-api` 8090, `hub-memory-api` 8091, `agent-service` 8093, `lab-authelia` 9091.
- **`clawvis` CLI** : absent du PATH (`command not found`) — le flux documenté `clawvis update …` n’est pas utilisable tel quel sur cette machine sans install symlink / `PATH`.

---

## 2. OpenClaw cron (`~/.openclaw/cron/jobs.json`)

OpenClaw stocke les jobs dans un **JSON unique** (`jobs.json`), pas un dossier de scripts par cron.

### Liens vers le dépôt Clawvis / instance dombot

- **Aucun job** ne référence explicitement `/home/lgiron/Lab/clawvis/scripts/…` ou `instances/dombot/`.
- La plupart des tâches ciblent **`~/.openclaw/skills/...`** (hub-refresh, kanban-implementer, knowledge-consolidator, git-sync, brain-maintenance, brain-pulse, self-improvement, proactive-innovation, etc.). La passerelle “repo → OpenClaw” attendue est donc **`clawvis skills sync`** (symlinks), pas des chemins directs vers `Lab/clawvis`.

### Écarts / risques constatés

| Job | Problème |
|-----|----------|
| **Hub Refresh** | Message : `~/.openclaw/skills/hub-refresh/scripts/run.sh` — sur devbox, **`hub_refresh_missing`** (fichier absent). Le job peut encore passer “ok” côté scheduler si l’agent ignore l’échec du script ; à corriger côté sync ou contenu du skill. |
| **Night Security Audit** | Chemin **`/home/lgiron/Lab/hub/system_audit.sh`** — répertoire **`/home/lgiron/Lab/hub` absent**. Cron cassé ou obsolète (reste hub-ldom). |
| **Kanban Implementer** | Utilise `~/.openclaw/skills/kanban-implementer/...` + `~/Lab/PROTOCOL.md` — cohérent avec skills OpenClaw, pas avec scripts core Clawvis. |
| Plusieurs jobs | Dernière erreur **`400 Budget has been exceeded`** (plafond 12) — risque opérationnel indépendant des chemins. |

### Fichier généré obsolète

- `instances/dombot/nginx/nginx-generated.conf` contient encore des chemins **`/home/lgiron/Lab/hub-ldom/...`** alors que **`hub-ldom` n’existe plus** sur le serveur. Ne pas se fier à ce fichier pour l’état réel du proxy.

---

## 3. Pourquoi Kanban et Settings ne sont pas les pages “Clawvis Vite”

### Config nginx **effective**

- Processus : `nginx -c /home/lgiron/Lab/clawvis/instances/dombot/logs/nginx-active.conf`.
- Extrait pertinent :

```nginx
location /kanban/ {
    alias /home/lgiron/Lab/clawvis/instances/dombot/public/kanban/;
}
location /settings/ {
    alias /home/lgiron/Lab/clawvis/instances/dombot/public/settings/;
}
```

### Cause

- Le Hub moderne est le **SPA** servi par le conteneur (`hub/nginx.conf` : `try_files $uri $uri/ /index.html` sur `/`).
- Les URLs **`/kanban/`** et **`/settings/`** sont interceptées **en amont** par nginx hôte et servent des **fichiers statiques datés** dans `instances/dombot/public/` (ex. `index.html` du **21 mars**), pas le build Docker du hub.
- Dans le core actuel, **`hub/public/`** ne contient plus de dossier `kanban/` (le produit cible est la SPA `hub/src` + build) : la copie instance est un **vestige hub-ldom / pré-SPA**.

### Piste de correction (hors périmètre de cet audit)

- Faire de `/kanban/` et `/settings/` des **`proxy_pass` vers `clawvis_hub`** (même upstream que `/hub/`), ou des redirections vers le routeur SPA (`/hub/` + hash ou pathname selon convention), pour aligner avec `hub/nginx.conf` et le contrat dev/prod du repo.

---

## 4. Test `git pull` (mise à jour core)

Commande exécutée sur devbox :

```bash
cd /home/lgiron/Lab/clawvis && git fetch origin && git pull origin main
```

### Résultat

- `fetch` : **OK** — `main` local `dbcb445` derrière `origin/main` **`99490b1`**.
- `pull` : **échec** — Git refuse la fusion :

> *Vos modifications locales … seraient écrasées … : `docker-compose.yml`*

### État du working tree (aperçu)

- Modifiés : `docker-compose.yml`, `hub/yarn.lock`, submodule `skills/self-improvement` dirty.
- Non suivis : backups `.env`, `docker-compose.yml.bak.bind`, `clawvis-cli/yarn.lock`, etc.

### Processus d’update recommandé (audit process)

1. **Inventaire** : `git status` ; noter overrides prod non commités.
2. **Sauvegarde** : copier ou committer sur une branche locale `prod-dombot` les fichiers qui doivent rester (surtout `docker-compose.yml` si bind ports / env).
3. **Isolation** : `git stash push -m "dombot pre-pull" -- docker-compose.yml hub/yarn.lock` (ou stash tout) ; pour submodule, `git submodule update` / commit séparé.
4. **Pull** : `git pull origin main`.
5. **Réapplication** : `git stash pop` et résoudre conflits ; vérifier `instances/dombot/docker-compose.override.yml` + `.env`.
6. **Rebuild** : `docker compose … build` + `up -d` selon override dombot.
7. **Post-merge hook** : si présent, `clawvis skills sync` (ou équivalent manuel des symlinks).
8. **CLI** : installer ou exposer `clawvis` dans le PATH pour industrialiser les étapes 6–7.

Tant que **`docker-compose.yml` root est modifié en prod** sans branche dédiée, **`git pull` ne sera pas idempotent**.

---

## 5. Synthèse actions prioritaires

1. Régénérer / versionner `nginx-active.conf` à partir d’un template dont **`HUB_ROOT` / alias Kanban-Settings** pointent vers le **hub container** (ou supprimer alias statiques).
2. **`clawvis skills sync`** + restaurer **`hub-refresh`** dans `~/.openclaw/skills` si le job doit rester.
3. Corriger ou retirer le job **Night Security** (chemin `Lab/hub/...` mort).
4. Nettoyer **`nginx-generated.conf`** ou le régénérer sans `hub-ldom` pour éviter la confusion.
5. Formaliser **update prod** : branche/stash + `pull` + rebuild ; ajouter **`clawvis` au PATH** sur devbox si le CLI est la référence.

---

*Audit rédigé à partir d’une session SSH sur `devbox` le 2026-03-29.*
