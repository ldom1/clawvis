# openclaw-dombot — sauvegarde configuration OpenClaw (Dombot)

Dépôt miroir privé sur GitHub : configuration runtime **OpenClaw** (sans secrets) pour restauration et audit.

## Architecture

| Élément | Rôle |
|--------|------|
| `openclaw.json` | Config principale (agents, modèles, canaux). Les secrets sont des références ou absents du dépôt. |
| `cron/jobs.json` | Crons OpenClaw (git-sync, kanban-implementer, etc.). |
| `agents/` | État agents/sessions (fichiers volumineux — backup opérationnel). |
| Skills réels | Code source sous **`Lab/clawvis/skills/`** et **`Lab/clawvis/instances/dombot/skills/`**. OpenClaw ≥ 2026.4 : éviter les **symlinks** `~/.openclaw/skills/*` → hors racine (sinon `doctor` spamme *Skipping skill path…*) ; préférer **`skills.load.extraDirs`** dans `openclaw.json` + chemins **absolus** dans `cron/jobs.json`. |

Le script **`Lab/clawvis/skills/git-sync/scripts/sync.sh`** (via extraDirs ou ancien chemin `~/.openclaw/skills/git-sync/...`) :

1. Copie `openclaw.json`, `cron/jobs.json` et `agents/` depuis `~/.openclaw/` vers `~/openclaw-dombot/`.
2. Commit + push vers `origin` (GitHub CLI ou git).
3. Enchaîne optionnellement `~/Lab/git-sync.sh` (autres dépôts Lab) — les erreurs partielles sur des repos Lab **ne font plus échouer** le backup OpenClaw.

## Intégrité

- Vérifier sur GitHub : commits récents, pas de divergence massive sur `main`.
- En local : `cd ~/openclaw-dombot && git fetch origin && git status` → à jour avec `origin/main`.

## Procédure de restauration (DRP)

1. **Machine neuve / home vide**  
   - Installer OpenClaw, `gh auth login` ou configurer `git` + accès SSH/HTTPS au dépôt privé.  
   - `git clone <url> ~/openclaw-dombot`

2. **Reinjecter la config**  
   - `cp ~/openclaw-dombot/openclaw.json ~/.openclaw/`  
   - `mkdir -p ~/.openclaw/cron && cp ~/openclaw-dombot/cron/jobs.json ~/.openclaw/cron/`  
   - `rsync -a ~/openclaw-dombot/agents/ ~/.openclaw/agents/` (ou copie sélective si trop lourd)

3. **Secrets**  
   - Recréer `.env`, tokens API, `auth*.json` depuis un gestionnaire de secrets (non versionnés).  
   - Vérifier les `SecretRef` dans `openclaw.json`.

4. **Skills Clawvis**  
   - Cloner `Lab/clawvis`. Soit **`skills.load.extraDirs`** vers `…/clawvis/skills` et `…/clawvis/instances/dombot/skills` + crons avec chemins absolus (recommandé OpenClaw récent), soit symlinks `~/.openclaw/skills/*` (peut déclencher des avertissements `doctor`).

5. **Redémarrer** le service OpenClaw / gateway selon ton installation.

6. **Contrôle**  
   - Lancer un job manuel léger (ex. logger) et vérifier les logs Hub + `dombot.jsonl`.

## Compaction (contexte LLM)

Pour réduire le coût des résumés de contexte, dans `openclaw.json` (référence OpenClaw 2026.x) :

```json
"agents": {
  "defaults": {
    "compaction": {
      "model": "openai/gpt-4o-mini"
    }
  }
}
```

Adapter le nom de modèle au routeur réel (ex. `anthropic/claude-haiku-4-5`).

---

*Généré / mis à jour par le skill `git-sync` — ne pas éditer les chemins sensibles à la main sur la machine de prod.*
