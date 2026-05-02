# clawvis-config-mirror — backup Clawvis dev config

Private GitHub mirror: **Clawvis** project files useful for restore (no API keys in repo).

## What gets copied

| Path in mirror | Source |
|----------------|--------|
| `clawvis-claude/` | `${CLAWVIS_ROOT}/.claude/` (rsync, secrets excluded by script rules) |
| `.env.example` | From repo root if present |
| `README.md` | This workflow description |

Skills and instance code stay in the **clawvis** repo; this mirror is only a thin config snapshot.

## Run

```bash
export CLAWVIS_ROOT=~/lab/clawvis   # if not auto-detected
${CLAWVIS_ROOT}/skills/git-sync/scripts/sync.sh
```

Optional: `GIT_SYNC_REPO=my-mirror` (default `clawvis-config-mirror` under `$HOME`).

After the Clawvis step, the script may run `~/Lab/git-sync.sh` for other Lab repositories.

## Restore

1. Clone this mirror next to your tools checkout.  
2. Copy `clawvis-claude/` into `${CLAWVIS_ROOT}/.claude/` (merge carefully; keep local secrets).  
3. Run **`clawvis skills sync`** (or your installer) so Claude Code sees `skills/` under the repo.
