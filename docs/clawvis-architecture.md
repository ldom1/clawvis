# Clawvis — Architecture & Positionnement

**Nom produit :** Clawvis (anciennement ClawPilot, anciennement LabOS)  
**Repo public :** `github.com/lgiron/clawvis` (open source, MIT)  
**Instance de référence :** `lab.dombot.tech` (VPS fixe, nginx, pas de Cloudflare tunnel)  
**Owner :** Ldom + DomBot  
**Statut :** Active Architecture (2026 Q1–Q4)

**Mission :** Transformer OpenClaw d'un outil dev-only → plateforme accessible à tous, avec orchestration multi-agents, observabilité et sécurité enterprise.

---

## 🗺️ Vue d'ensemble — Ce qu'est Clawvis

Clawvis est **la plateforme complète** qui se pose au-dessus d'OpenClaw. Ce n'est pas un concurrent d'OpenClaw — c'est ce qui le rend utilisable par tous et orchestrable à grande échelle.

```
┌──────────────────────────────────────────────────────────┐
│           hub-ldom (repo PRIVÉ — dombot.tech)            │
│         instances/ldom/ : Authelia · nginx perso         │
│          projets perso · scripts · .env.local            │
│        (ne contient QUE ce qui est spécifique à Ldom)    │
└────────────────────┬─────────────────────────────────────┘
                     │ git upstream = clawvis public
                     │ (pull updates sans effort)
┌────────────────────▼─────────────────────────────────────┐
│                    CLAWVIS (public)                      │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  hub/       │  │  hub-core/   │  │  skills/       │  │
│  │  (template  │  │  (Python :   │  │  (scripts +    │  │
│  │   frontend  │  │  identity,   │  │   prompts      │  │
│  │   nginx)    │  │  RBAC,       │  │   packagés)    │  │
│  │             │  │  adapters,   │  │                │  │
│  │             │  │  registry)   │  │                │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  kanban/    │  │  openclaw/   │  │  vault-        │  │
│  │  (API CRUD  │  │  (runtime    │  │  template/     │  │
│  │   + deps)   │  │   wrapper)   │  │  (Obsidian     │  │
│  │             │  │              │  │   pré-config)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                          │
│  instances/                                              │
│  ├── example/   ← template commité (valeurs fictives)   │
│  └── ldom/      ← dans hub-ldom (privé, gitignored)     │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│              OpenClaw Core (openclaw.ai)                 │
│         Runtime agent — community / open source          │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────┐
│     LLM Layer (Claude / MammouthAI / Mistral / local)    │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 Structure du repo Clawvis

```
clawvis/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── README.md
├── LICENSE
├── install.sh                    ← One-click setup (goal: curl | bash)
├── docker-compose.yml            ← Stack complète (hub, kanban, orchestrator)
│
├── hub/                          ← Template frontend (nginx + HTML)
│   ├── nginx.conf                ← Config nginx templatisée
│   ├── public/                   ← Assets statiques
│   └── [placeholder projets]     ← À surcharger dans le hub privé
│
├── hub-core/                     ← Bibliothèque Python (cœur métier)
│   ├── security/
│   │   ├── identity.py           ← AgentIdentity (Ldom, DomBot, Viewer)
│   │   ├── rbac.py               ← require_capability + UnauthorizedError
│   │   └── network.py            ← unrestricted / restricted / allowlist
│   ├── agents/
│   │   ├── registry.py           ← AgentRegistry (health, métriques, sélection)
│   │   ├── base.py               ← IAgentAdapter (interface)
│   │   ├── openclaw_adapter.py   ← OpenClaw local (cost=0)
│   │   ├── claude_adapter.py     ← Claude API
│   │   ├── mammouth_adapter.py   ← MammouthAI (fallback Claude)
│   │   └── gemini_adapter.py     ← Gemini
│   ├── api_fallback.py           ← with_mammouth_fallback() (seuil 75%)
│   ├── token_cache.py            ← Cache tokens (in-memory + Redis option)
│   └── main.py                   ← FastAPI app
│
├── kanban/                       ← API CRUD tâches + dépendances
│   ├── Dockerfile
│   └── core/
│
├── skills/                       ← Skills packagés pour DomBot / utilisateurs
│   ├── morning-briefing.py       ← Briefing quotidien Telegram
│   ├── hub-refresh.py            ← Rafraîchit JSON système (cron 1h)
│   ├── knowledge-consolidator/   ← Consolidation Obsidian vault
│   └── [prompts/]                ← Personas + instructions système
│
├── memory/                       ← Placeholder (doc uniquement)
│   └── README.md                 ← Pointe vers ~/.openclaw/workspace/memory
│
├── openclaw/                     ← Wrapper + config OpenClaw
│   └── ...
│
├── core-tools/                   ← Utilitaires partagés
│   └── ...
│
├── docs/                         ← Documentation technique
│   └── ...
│
├── scripts/                      ← Scripts d'installation + maintenance
│   └── ...
│
└── vault-template/               ← Template Obsidian pré-configuré
    ├── .obsidian/                ← Config plugins + thème
    └── [structure notes]         ← Dossiers pré-créés pour nouveaux utilisateurs
```

---

## 🔗 Pattern Instances — hub-ldom ↔ clawvis

### Le principe en une phrase

> Clawvis est la base. `instances/ldom/` est ce qui te rend unique. Tout le reste est partagé.

### Structure instances/

```
clawvis/
└── instances/
    ├── README.md                     ← "Fork this folder for your own instance"
    ├── example/                      ← Template commité (valeurs fictives)
    │   ├── docker-compose.override.yml
    │   ├── nginx.conf
    │   └── .env.example
    └── ldom/                         ← Dans hub-ldom (repo privé)
        ├── docker-compose.override.yml   ← Authelia + projets perso
        ├── nginx/
        │   ├── nginx.conf                ← Routes privées (debate-arena, messidor...)
        │   └── authelia.conf
        ├── authelia/
        ├── scripts/
        │   ├── session-end-tracker.sh
        │   └── system_audit.sh
        └── .env.local                    ← Clés API, IPs (gitignored)
```

### Ce qui va où — règle simple

| Élément | Où | Pourquoi |
|---------|-----|---------|
| hub-core, skills, kanban | `clawvis/` racine | Utile à tous |
| vault-template, install.sh | `clawvis/` racine | Utile à tous |
| nginx de base | `clawvis/hub/nginx.conf` | Template vide |
| Authelia | `instances/ldom/authelia/` | Toi uniquement |
| Routes nginx privées | `instances/ldom/nginx/` | Toi uniquement |
| debate-arena, messidor | hors repo clawvis | Projets perso |
| Clés API, IPs | `instances/ldom/.env.local` | Secrets — jamais commités |

### Setup Git — deux remotes

```
repo PRIVÉ : github.com/lgiron/hub-ldom
  ├── remote origin   → github.com/lgiron/hub-ldom  (push tes customisations)
  └── remote upstream → github.com/lgiron/clawvis   (pull les updates clawvis)
```

```bash
# Installation initiale
git clone https://github.com/lgiron/clawvis hub-ldom
cd hub-ldom
git remote rename origin upstream
git remote add origin git@github.com:lgiron/hub-ldom.git
cp -r instances/example instances/ldom
echo "instances/ldom/.env.local" >> .gitignore
git push -u origin main
```

### Recevoir les updates clawvis

```bash
git pull upstream main
# Tes fichiers dans instances/ldom/ ne sont jamais touchés par upstream
```

Alias recommandé :
```bash
alias clawvis-update='cd ~/clawvis && git pull upstream main && docker compose -f docker-compose.yml -f instances/ldom/docker-compose.override.yml up -d'
```

### Contribuer vers clawvis

```bash
# Quand tu améliores quelque chose de générique (skill, hub-core, template...)
git checkout -b feat/nom-amélioration
# ... commits dans clawvis/ (pas dans instances/ldom/) ...
git push origin feat/nom-amélioration
# Ouvrir une PR vers upstream (clawvis public)
```

La règle : si quelque chose pourrait être utile à quelqu'un d'autre → racine clawvis + PR. Si c'est spécifique à toi → `instances/ldom/`, jamais de PR.

### Docker — base + override

```bash
# Clawvis seul (nouveaux utilisateurs)
docker compose up

# Instance Ldom complète
docker compose -f docker-compose.yml -f instances/ldom/docker-compose.override.yml up
```

`instances/ldom/docker-compose.override.yml` ajoute : Authelia, routes nginx privées, projets perso (debate-arena, messidor...) — sans jamais modifier le `docker-compose.yml` de base.

### Migration depuis l'état actuel

```
~/hub/authelia/     →  clawvis/instances/ldom/authelia/
~/hub/nginx.conf    →  clawvis/instances/ldom/nginx/nginx.conf
~/hub/scripts/      →  clawvis/instances/ldom/scripts/
~/hub/data/         →  volume Docker clawvis-data
~/hub/logs/         →  volume Docker ou ~/.openclaw/logs/
```

---

## 🧩 Les quatre couches de Clawvis

### Couche 1 — Opérationnelle : Hub + Kanban + Logs
**Statut :** ✅ Conçu et documenté (2026-03-12)

Cockpit intégré pour l'exécution de tâches mono-agent avec transparence totale.

| Surface | Rôle |
|---------|------|
| **Hub** (dashboard) | Santé système, métriques temps réel, actions rapides |
| **Kanban** (API) | CRUD tâches, enforcement des dépendances, suivi statut |
| **Logs** (audit) | Historique immutable, confidence scoring, traçabilité |

**Boucle agent :**
```
Utilisateur → Hub (nouvelle tâche)
  ↓
Agent → Kanban (poll for work)
  ↓
Agent → Confidence check (>80% / 50-80% / <50%)
  ↓
Agent → Log action (AVANT exécution, immutable)
  ↓
Agent → Exécute le travail
  ↓
Agent → Met à jour Kanban + Log résultat
  ↓
Hub → Affichage temps réel (SSE / polling 60s)
```

**Confidence scoring :**
- `>80%` ✅ Auto-proceed
- `50–80%` 🟡 Verify before archiving
- `<50%` 🔴 Manuel review requis

---

### Couche 2 — Orchestration : Multi-Agent Workflows
**Statut :** 🔄 En cours (Phase 1 → 2026-03-28)

Moteur de coordination de workflows multi-agents avec routing intelligent.

```
Agent Runtimes
├── OpenClaw   (self-hosted, gratuit, rapide)
├── Claude     (qualité, via API)
├── MammouthAI (fallback Claude, budget)
├── Gemini     (cheap, volume)
└── Custom     (via IAgentAdapter)
        ↓
AgentRegistry (health, coût, qualité par agent)
        ↓
Workflow Engine (séquentiel / parallèle / branching)
        ↓
Skills Marketplace (workflows réutilisables)
        ↓
Observability Dashboard (coût par agent par tâche)
```

**Exemple de workflow YAML :**
```yaml
name: "Draft-Review-Polish"
steps:
  - agent: openclaw
    task: "Write initial code"
  - agent: claude
    task: "Review and suggest improvements"
    context:
      code: ${{ steps[0].output }}
  - agent: openclaw
    task: "Refactor based on feedback"
    context:
      code: ${{ steps[0].output }}
      feedback: ${{ steps[1].output }}
mode: sequential
aggregation: last
```

---

### Couche 3 — Accessibilité : Démocratisation
**Statut :** 🔄 Roadmap définie (2026-03-20+)

Rendre Clawvis installable et utilisable sans compétences CLI.

| Objectif | Mécanisme |
|----------|-----------|
| One-click deployment | `install.sh` + template Hostinger |
| Pas de CLI requis | Web UI (setup wizard, config visuelle) |
| Multi-LLM | Abstraction provider (Claude / Mistral / local) |
| Vault pré-configuré | `vault-template/` Obsidian livré avec Clawvis |

---

### Couche 4 — Sécurité : Enterprise
**Statut :** 📋 Post-MVP

| Composant | Rôle |
|-----------|------|
| **Authelia** (hub privé) | SSO single-user aujourd'hui (Ldom uniquement) |
| **RBAC** (`hub-core/security/rbac.py`) | Owner / Agent / Viewer + capabilities |
| **Network policy** (`network.py`) | unrestricted / restricted / allowlist |
| **NemoClaw** (futur) | Compliance NVIDIA, certification enterprise |
| **Audit trail** | Logs immutables avec `agent_identity` sur chaque entrée |

---

## 🛡️ Identité & RBAC

```python
# Rôles actuels
class AgentRole(Enum):
    OWNER       = "OWNER"        # Ldom — veto total
    ORCHESTRATOR = "ORCHESTRATOR" # DomBot — exécute + orchestre
    VIEWER      = "VIEWER"       # Read-only

# Chaque skill injecte son identité
AGENT_ID=dombot AGENT_ROLE=ORCHESTRATOR skill.py
```

Chaque action écrite dans `dombot.log` et `dombot.jsonl` inclut `agent_identity`.

---

## 💾 Flux de données — Source of Truth

```
Agent Action
  ↓
1. Log action (immutable — dombot.log + dombot.jsonl)
  ↓
2. Update Kanban (métadonnées tâche)
  ↓
3. Rebuild .md (Obsidian vault — source of truth)
  ↓
4. Hub polls JSON / reçoit SSE
  ↓
5. Dashboard rafraîchi (< 5s)
```

**Mémoire des agents :**  
`~/.openclaw/workspace/memory/` — orchestrée par OpenClaw directement (Clawvis ne gère pas la mémoire, il s'appuie sur le runtime).

---

## 📊 Positionnement marché

### Clawvis vs concurrents

| Aspect | Concurrents | Clawvis |
|--------|-------------|---------|
| Multi-agent | ❌ Single agent | ✅ Tout agent via adapters |
| Routing | ❌ Manuel | ✅ Automatique (coût × qualité) |
| Transparence | ❌ Boîte noire | ✅ Hub + Logs + Confidence |
| Coût visible | ❌ Caché | ✅ Par agent par tâche |
| Vendor lock-in | ❌ Oui | ✅ Non (IAgentAdapter pluggable) |
| Accessible | ❌ CLI only | ✅ Web UI + 1-click deploy |

### Écosystème (Clawvis est complémentaire, pas concurrent)

| Composant | Rôle | Créateur |
|-----------|------|---------|
| **OpenClaw** | Runtime agent (personal/community) | Peter Steinberger → OpenAI |
| **NemoClaw** | Security wrapper enterprise pour OpenClaw | NVIDIA |
| **Clawvis** | Orchestration + accessibilité AU-DESSUS des deux | Ldom |

---

## 📋 Roadmap

### Phase 1 — Opérationnel ✅ DONE (2026-03-12)
- Hub dashboard + Kanban API + Logs
- Confidence scoring + audit trail
- Write-through guarantees

### Phase 2 — Orchestration 🔄 IN PROGRESS (2026-03-14 → 2026-06-06)

| Phase | Dates | Focus |
|-------|-------|-------|
| 1 | 03-14 → 03-28 | API + OpenClaw adapter |
| 2 | 03-29 → 04-11 | Multi-agent (Claude + MammouthAI) |
| 3 | 04-12 → 04-25 | Workflow engine (YAML) |
| 4 | 04-26 → 05-09 | Skills marketplace |
| 5 | 05-10 → 05-23 | Observability + scaling |
| 6 | 05-24 → 06-06 | Launch + marketing |

### Phase 3 — Accessibilité 📋 TODO (2026-03-20+)
- One-click Hostinger deployment
- Web UI setup wizard (sans CLI)
- Multi-LLM support complet
- vault-template finalisé

### Phase 4 — Enterprise 📋 Post-MVP
- NemoClaw integration
- Multi-tenant (SaaS)
- Certifications compliance

---

## 🔧 Prochaines étapes immédiates

### Court terme (prochaines sessions)

**1. Tester la vraie clé MammouthAI**
- Régénérer sur mammouth.ai → Settings → API Keys
- `uv run pytest tests/test_real_providers.py -v`

**2. Hub dashboard consomme les JSON en temps réel**
- Câbler `api/providers.json` + `api/system.json` côté frontend
- Polling 60s (cohérent avec cron hub-refresh)

**3. Réponse Telegram formatée depuis hub-refresh**
- Format cible : `🖥️ Hub | CPU 8% RAM 67% | MammouthAI €6.97/€12 | Claude 0%`

**4. RBAC dans tous les skills existants**
- Pattern : injecter `AGENT_ID=dombot AGENT_ROLE=ORCHESTRATOR` dans chaque skill

**5. api_fallback branché dans les skills qui appellent Claude**
- Candidats : `morning-briefing.py`, `knowledge-consolidator`, `proactive-innovation`
- Auto-switch Claude → MammouthAI si rate limit ≥ 75%

**6. Migrer hub privé → pattern instances/ldom** ⚡ Priorité
- Créer `github.com/lgiron/hub-ldom` (privé)
- Setup deux remotes (upstream = clawvis, origin = hub-ldom)
- Déplacer authelia + nginx + scripts → `instances/ldom/`
- Tester `docker compose -f ... -f instances/ldom/...` sur le VPS
- Supprimer l'ancien repo `hub` une fois validé

---

## ✅ Accompli (2026-03-17)

| Task | Status |
|------|--------|
| `hub_core/security/identity.py` (AgentIdentity + rôles) | ✅ Done |
| `hub_core/security/rbac.py` (require_capability + UnauthorizedError) | ✅ Done |
| `hub_core/security/network.py` (unrestricted/restricted/allowlist) | ✅ Done |
| `hub_core/agents/registry.py` (AgentRegistry + health) | ✅ Done |
| `IAgentAdapter` interface (base.py) | ✅ Done |
| `OpenClawAdapter` (local exec, cost=0) | ✅ Done |
| Skill `hub-refresh` (cron 1h + Telegram on-demand) | ✅ Done |
| Logs incluent `agent_identity` (dombot.log + dombot.jsonl) | ✅ Done |
| `api_fallback.py` avec `with_mammouth_fallback()` | ✅ Done |

---

## 📚 Documentation map

| Doc | Contenu |
|-----|---------|
| **[[clawvis-architecture]]** ← ce fichier | Vue d'ensemble, structure, roadmap |
| **[[labos-integration-hub-kanban-logs]]** | Couche opérationnelle — détails techniques complets |
| **[[hub-orchestration-architecture]]** | Workflow engine, adapters, skills marketplace |
| **[[openclaw-architecture]]** | Runtime OpenClaw, tools, deployment |
| **[[lead-generation]]** | Positionnement marché + narrative |
| **[[token-optimization-study]]** | Case study — 70% réduction tokens |

---

*"Clawvis n'est pas un outil. C'est l'infrastructure qui rend l'intelligence agentique accessible, observable et orchestrable — pour tout le monde."*  
— Ldom + DomBot, 2026-03-21

**Créé :** 2026-03-21  
**Statut :** Architecture active — Phase 2 en cours  
**Target :** MVP Production 2026-06-06
