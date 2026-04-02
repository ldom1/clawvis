# docs/PITFALLS.md

> Bugs connus, dettes techniques et points de friction documentés.
> Mis à jour à chaque session de debug significative.
> Pour l'architecture → `docs/ARCHITECTURE.md`

---

## Pitfalls production (ADR 0004)

| # | Symptôme | Cause | Fix |
|---|----------|-------|-----|
| 1 | 500 Kanban/Memory | Symlink Docker cassé | Volume override explicit dans `docker-compose.override.yml` |
| 2 | Page noire | Vite `/assets/` non routé par nginx | Bloc `location /assets/` AVANT `/hub/` |
| 3 | Logo 404 | `hub/public/` fichiers root non routés | nginx regex location pour root statics |
| 4 | nginx HUP silencieux | `envsubst` sans export + sans scope | `export` + scope explicite |
| 5 | Page noire (encore) | Container non rebuild après JS changes | `build` + `up --force-recreate` |
| 6 | 0 logs | `Path.home()` = `/` si `HOME` absent | `HOME=/home/lgiron` + volume logs openclaw |
| 7 | 0 projets | `projects_root` = chemin inexistant | Corriger le chemin + volume mount |
| 8 | `/chat/` inaccessible | Hash routing vs pathname SPA | Proxy `location /chat/` → clawvis_hub |
| 9 | OpenClaw Node v22+ | `setup_20.x` non supporté | `setup_22.x` dans Dockerfile |
| 10 | EACCES UID 1000 | State files hôte | `user: root` + mount identique |
| 11 | Port 8092 conflit | `spendlens_api` sur 8092 | `AGENT_PORT=8093` dans `.env` |
| 12 | Chat `[CLAWVIS:AUTH]` | Tokens OAuth, pas API keys | `preferred_provider=openclaw` dans agent-config.json |
| 13 | `/project/<slug>` 404 | `location /project/` manquant nginx | Ajouté dans template 2026-03-28 |
| 14 | Containers sans override | `docker compose up` sans override → symlink cassé | Toujours lancer avec `-f instances/ldom/docker-compose.override.yml` |
| 15 | Cron `Channel is required` | Pas de canal par défaut | `"channel": "telegram"` dans delivery des jobs |
| 16 | Runtime banner toujours visible | SPA ignorait l'état backend | Chip collapsible vert quand configuré |
| 17 | Nginx route orpheline après delete projet | `_cleanup_nginx_route()` inactif sans env var | Actif si `NGINX_PROJECTS_D` défini |
| 18 | Kanban / Logs / Settings sans changements SPA | `location /kanban/` + `/settings/` en `alias` vers `instances/dombot/public/` | `nginx/nginx.conf` : `proxy_pass` Hub + `include …/snippets/spa-hub-prefixes.conf` (`^~` sur les préfixes SPA, **avant** `projects.d`) ; `scripts/render-nginx.sh` |
| 19 | `500` sur `/hub/` | Vieux `location /hub/` + `alias` ou chemin invalide ; l’UI est à `/` | `spa-hub-prefixes.conf` + `hub/nginx.conf` : `^~ /hub/` → redirect 301 vers `/` ou `/…` ; supprimer tout `alias` résiduel dans `projects.d` |
| 20 | Crons OpenClaw (ex. hub-refresh 1h) ne partent pas | **`openclaw-gateway`** en échec (restart en boucle) — config invalide après upgrade CLI | `journalctl --user -u openclaw-gateway.service` ; `PATH=~/.npm-global/bin:$PATH openclaw doctor --fix` ; vérifier `systemctl --user status openclaw-gateway` **active (running)** stable |
| 21 | `doctor` : *Skipping skill path that resolves outside its configured root* (répété) | Symlinks `~/.openclaw/skills/<name>` → `Lab/clawvis/...` : la racine gérée est `~/.openclaw/skills`, OpenClaw ignore les cibles hors racine | **`clawvis skills sync`** (`scripts/sync-openclaw-skills-dirs.sh`) : `jq` + chemins absolus `skills/` + `instances/<INSTANCE>/skills/`, supprime symlinks managés, puis **`openclaw gateway restart`**, **`openclaw skills list`**, **`openclaw doctor`**. Crons : chemins absolus repo (pas `~/.openclaw/skills/…`) |
| 22 | `collect.sh` / crons skills : *Commande non autorisée* (OpenClaw) | Politique d’exécution / allowlist des **tools** ou du **shell** côté passerelle qui bloque `uv`, `curl`, `bash`, chemins hors liste | Vérifier `openclaw doctor` et la config cron **tools** (OpenClaw 2026.x) ; préférer jobs **`exec`** / script shell direct sur la machine plutôt que tout passer par un tour agent si la policy est stricte |
| 23 | `skill-tester` : 0 tests, `~/.openclaw/skills` vide | Après **`clawvis skills sync`** (extraDirs), il n’y a plus de copies/symlinks sous `~/.openclaw/skills` | Lancer avec **`CLAWVIS_ROOT=$HOME/Lab/clawvis INSTANCE_NAME=dombot`** (ou **`SKILL_TEST_ROOTS="…/skills …/instances/dombot/skills"`**) : `bash skills/skill-tester/scripts/test-all.sh` |
| 24 | **500** sur tout le lab (`lab.dombot.tech` / `:8088`) | **`auth_request` Authelia → 400** : `X-Original-URL` en **`http://`** alors que le TLS est au reverse proxy (nginx local voit `$scheme` = http) | Template `instances/dombot/nginx/nginx.conf` : **`https`** forcé pour Authelia + **`map`** `lab_x_forwarded_proto` vers le Hub ; `render-nginx.sh --reload` |
| 25 | **500** après correctif #24 ; logs Authelia **« authelia url lookup failed »** | **AuthRequest** ne déduit plus l’URL du portail si **`session.cookies[]` + `authelia_url`** manquent (upgrade 4.38+) | **`configuration.yml`** : `session.cookies` avec `authelia_url: https://lab.dombot.tech/authelia/` ; **ou** nginx : `proxy_pass …/auth-request?authelia_url=https://$host/authelia/;` (déjà dans le template) |
| 26 | **Crons OpenClaw `exec denied`** — `security=allowlist ask=on-miss askFallback=deny` | Mode allowlist par défaut : les crons ne peuvent pas attendre une approbation interactive, `askFallback=deny` bloque tout script hors allowlist | Dans `~/.openclaw/openclaw.json` → `tools.exec: {security: "full", ask: "off"}` ; dans `~/.openclaw/exec-approvals.json` → `defaults: {security: "full", ask: "off"}` ; puis `openclaw gateway restart`. Vérifié : `openclaw approvals get --gateway` affiche `security=full, ask=off` |
| 27 | **`kanban/Dockerfile` — `uv sync --no-dev` échoue** avec `dombot-hub-core is not a workspace member` | `kanban/Dockerfile` copiait `hub-core/` et `kanban/` mais pas le `pyproject.toml` + `uv.lock` racine qui définissent le workspace uv | Ajouter `COPY pyproject.toml ./` et `COPY uv.lock ./` AVANT `COPY hub-core/ ./hub-core/` dans `kanban/Dockerfile` |
| 28 | **Containers kanban-api / hub-memory-api exitent (255)** — `exec /clawvis/kanban/.venv/bin/uvicorn: no such file or directory` | Avec le workspace uv, le venv est créé à la racine `/clawvis/.venv`, pas dans `/clawvis/kanban/.venv` | Remplacer tous les chemins `/clawvis/kanban/.venv/bin/` par `/clawvis/.venv/bin/` dans `docker-compose.yml` et `kanban/Dockerfile` CMD |
| 29 | **Page blanche sur `lab.dombot.tech`** — Authelia portal vide, JS bundles ne chargent pas (`upstream prematurely closed connection`) | VPS nginx sans `proxy_buffering` : mode streaming ; les JS bundles Authelia (~314 KB) et Hub assets dropent via Tailscale DERP relay. HTML (2 KB) passe, gros fichiers non. | VPS `/etc/nginx/sites-enabled/lab.dombot.tech` : `proxy_buffering on; proxy_buffer_size 128k; proxy_buffers 8 256k; proxy_busy_buffers_size 512k; proxy_read_timeout 120s;` puis `nginx -s reload` |

---

## Bugs corrigés — session 2026-03-28

1. **hub-core pylint E0211** : `setup_runtime.py:21` — `get_providers()` manquait `@staticmethod` → corrigé
2. **Hub Prettier** : `src/main.js`, `src/style.css`, `vite.config.js` non formatés → corrigé (`yarn --cwd hub format`)
3. **install.sh — `rg` non-standard** : `migrate_memory_if_needed` utilisait `rg` → remplacé par `find`
4. **install.sh — Docker sans message utile** : Erreur vague → message clair avec lien install + `docker info`
5. **install.sh — Node version** : Aucune vérification → guard Node >= 18 ajouté
6. **install.sh — yarn absent en dev mode** : Pas de fallback → `corepack enable` automatique
7. **docker-compose.yml — label obsolète** : `app=clawpilot` → `app=clawvis`
8. **hub/src/main.js — compteur services** : `/openclaw/` comptabilisé "down" → marqué `optional: true`
9. **hub/src/main.js — i18n FR accents** : `"Parametres"` → `"Paramètres"`, `"A configurer"` → `"À configurer"`, etc.

---

## Points de friction non résolus (priorité)

### Critique — bloque le mode Franc

**Kanban API absent du docker-compose**
En mode `docker` (mode Franc), le tableau Kanban est inutilisable : tous les appels `/api/kanban/*` retournent 404.
→ Fix : ajouter service `kanban-api` basé sur `hub-core` au docker-compose + proxy nginx dans conteneur hub.

### Important

**Quartz Brain build**
`scripts/build-quartz.sh` dépend d'un submodule optionnel. Si absent, le Brain n'affiche rien sans message d'erreur clair.
→ Fix : dégradation gracieuse — afficher le renderer Python léger si Quartz absent.

**`clawvis setup provider` non implémenté**
Commande CLI post-install pour configurer le provider depuis le terminal. Mentionnée dans CLAUDE.md mais inexistante.
→ Fix : implémenter dans `clawvis-cli/` comme commande post-install.

### Mineur

**`clawvis skills sync` (Phase 2A.7)**
Symlinks skills OpenClaw non synchronisés automatiquement. Doit rendre les skills disponibles dans le chat.
→ Prochaine étape avant Phase 2B.

---

## Audit technique — 2026-03-24

> Extrait des findings techniques sur la dette d'architecture.

**Gap architecture réelle du stack :**
- Dev mode : Vite sur `HUB_PORT`, proxy Vite `/api/kanban/*` → Kanban API uvicorn (8090)
- Docker mode : nginx sert `hub/dist/`. **Kanban API non présente dans docker-compose** — gap critique
- Brain = Logseq web app (`ghcr.io/logseq/logseq-webapp`) sur `MEMORY_PORT` — embed iframe

**Règles d'outillage à ne pas oublier :**
- Hub → Yarn Berry 4 uniquement (`yarn --cwd hub`) — jamais npm
- CLI → npm (`npm ci`)
- Kanban API + hub-core → uv uniquement — jamais pip
- CI gate → `bash tests/ci-all.sh` retourne 0 avant tout merge

---

## Template : ajouter un pitfall

```markdown
| N | <symptôme observable> | <cause racine> | <fix appliqué ou à appliquer> |
```

Règle : un pitfall documenté = symptôme + cause + fix. Pas de "à investiguer" sans au moins la cause suspectée.
