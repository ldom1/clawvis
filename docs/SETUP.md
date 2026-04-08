# Clawvis setup

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash
```

Clones the repo to `~/.clawvis`, runs the interactive wizard, and starts the stack.

**Direct git clone:**

```bash
git clone https://github.com/ldom1/clawvis ~/.clawvis
cd ~/.clawvis && ./install.sh
```

---

## Prerequisites

### Mode prod (Docker — default)

| Tool | Why |
|------|-----|
| Git | Cloned by `get.sh` automatically |
| Docker Engine 24+ or Desktop | Runs the full stack |

### Mode dev (local)

| Tool | Version | Why |
|------|---------|-----|
| Node.js | >= 18 | Vite dev server |
| npm | bundled | Dependencies |
| Yarn 4 (corepack) | 4.x | Hub build — `corepack enable` |
| uv | latest | Kanban API + hub-core |

---

## Wizard steps

`install.sh` walks you through five steps:

1. **Instance name** — defaults to `$USER`. Creates `instances/<name>/`.
2. **Run mode** — `dev`, `prod`, or `minimal` (see below).
3. **Memory** — local fresh directory, or symlink to an existing brain path.
4. **Ports** — Hub (8088), Brain (3099), Kanban API (8090).
5. **Quartz** — auto-builds the Brain static site if `git` + `node` + `npm` are present.

---

## Run modes

| Mode | What it does | Docker? |
|------|-------------|---------|
| `dev` | Vite dev server + uvicorn — code changes reload live | No |
| `prod` | Full Docker stack — `docker compose up` | Yes |
| `minimal` | Creates instance structure only, does not start services (`--no-start`) | Yes |

---

## Memory types

| Type | When to use |
|------|-------------|
| `local` | Fresh install — creates `instances/<name>/memory/` |
| `symlink` | You already have a brain directory (Obsidian vault, etc.) — wizard asks for the path and creates a symlink |

---

## Non-interactive mode (CI / scripted)

```bash
./install.sh --non-interactive --instance myname --mode prod
```

All flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--non-interactive` | — | Skip all prompts |
| `--instance <name>` | `$USER` | Instance name |
| `--mode <dev\|prod\|minimal>` | `prod` | Run mode |
| `--brain-path <path>` | — | Existing memory path (implies `symlink`) |
| `--memory-type <local\|symlink>` | `local` | Memory type |
| `--hub-port <port>` | `8088` | Hub port |
| `--memory-port <port>` | `3099` | Brain port |
| `--kanban-api-port <port>` | `8090` | Kanban API port |
| `--projects-root <path>` | `~/lab_perso/projects` | Projects root |
| `--no-start` | — | Create structure only, skip service launch |

---

## Environment variables (get.sh)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWVIS_DIR` | `~/.clawvis` | Install directory |
| `CLAWVIS_REPO_URL` | GitHub URL | Clone source (use `file:///path` to test locally) |
| `CLAWVIS_REF` | empty (default branch) | Branch or tag to clone |
| `CLAWVIS_LAST_LOG` | `/tmp/clawvis_last.log` | Captured output from background steps |

## Environment variables (install.sh)

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWVIS_SKIP_QUARTZ` | `0` | Set to `1` to skip Quartz build |
| `CLAWVIS_LAST_LOG` | `/tmp/clawvis_last.log` | Captured output from background steps |

---

## Post-install

After install, the `clawvis` CLI shim is added to `~/.local/bin/`. If it is not yet on your `PATH`, reload your shell:

```bash
source ~/.zshrc   # or ~/.bashrc
```

**Service URLs (default ports):**

| Service | URL |
|---------|-----|
| Hub | http://localhost:8088 |
| Kanban | http://localhost:8088/kanban/ |
| Brain | http://localhost:8088/memory/ |
| Logs | http://localhost:8088/logs/ |
| Settings | http://localhost:8088/settings/ |

---

## AI runtime

No key is required at install time. Configure post-install in **Settings → AI Runtime** or in `.env`:

```bash
CLAUDE_API_KEY=sk-ant-...
OPENCLAW_BASE_URL=http://host:18789
```

See [Architecture](ARCHITECTURE.md) for the full provider routing.
