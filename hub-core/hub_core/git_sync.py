"""Git sync helpers for Lab repos (status JSON + optional sync script)."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Sequence

from loguru import logger

from hub_core.config import HUB_API_DIR, LAB_DIR


DEFAULT_REPOS: tuple[str, ...] = (
    "debate-arena",
    "hub",
    "optimizer-arena",
    "techspend",
)
# Repos under subdirs (name -> path relative to LAB_DIR)
REPO_PATH_OVERRIDES: dict[str, str] = {"techspend": "poc/techspend"}

GIT_STATUS_JSON = HUB_API_DIR / "git-status.json"


def _check_repo_status(repo_path: Path) -> tuple[bool, str]:
    """Return (synced, info_or_error)."""
    try:
        # Uncommitted changes?
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            return False, "Uncommitted changes"

        # Fetch latest
        subprocess.run(
            ["git", "fetch", "-q"],
            cwd=repo_path,
            timeout=5,
        )

        # Current branch
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()

        ahead = subprocess.run(
            ["git", "rev-list", f"origin/{branch}..HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        behind = subprocess.run(
            ["git", "rev-list", f"HEAD..origin/{branch}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()

        synced = not ahead and not behind
        return synced, branch if synced else "Out of sync"
    except Exception as e:  # pragma: no cover - defensive
        return False, str(e)


def get_git_status(repos: Sequence[str] | None = None) -> dict:
    repos = tuple(repos) if repos is not None else DEFAULT_REPOS
    data: dict = {
        "lab_dir": str(LAB_DIR),
        "last_sync": datetime.now().isoformat(),
        "all_repos_synced": True,
        "repos": {},
    }

    for name in repos:
        repo_path = LAB_DIR / REPO_PATH_OVERRIDES.get(name, name)
        if not (repo_path / ".git").is_dir():
            logger.warning("Repo {} not found or not a git repo", repo_path)
            data["repos"][name] = {
                "synced": False,
                "branch": None,
                "error": "Not a git repo",
            }
            data["all_repos_synced"] = False
            continue

        synced, info = _check_repo_status(repo_path)
        data["repos"][name] = {
            "synced": synced,
            "branch": info if synced else None,
            "error": None if synced else info,
        }
        if not synced:
            data["all_repos_synced"] = False

    return data


def write_git_status(repos: Sequence[str] | None = None) -> dict:
    """Compute and write git status JSON, return the payload."""
    status = get_git_status(repos)
    HUB_API_DIR.mkdir(parents=True, exist_ok=True)
    GIT_STATUS_JSON.write_text(json.dumps(status, indent=2))
    logger.info("Wrote git status to {}", GIT_STATUS_JSON)
    return status


def run_git_sync_script() -> int:
    """Run the Lab-level git-sync.sh script if present."""
    script = LAB_DIR / "git-sync.sh"
    if not script.exists():
        logger.error("git-sync.sh not found at {}", script)
        return 1

    logger.info("Running git sync script: {}", script)
    result = subprocess.run(
        ["/usr/bin/env", "bash", str(script)],
        cwd=LAB_DIR,
    )
    if result.returncode != 0:
        logger.error("git-sync.sh failed with code {}", result.returncode)
    return result.returncode


def cli(sync: bool = False) -> int:
    """Convenience entry for CLI command."""
    if sync:
        code = run_git_sync_script()
        if code != 0:
            return code

    status = write_git_status()
    return 0 if status.get("all_repos_synced") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli())
