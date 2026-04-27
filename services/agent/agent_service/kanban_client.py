"""HTTP client for Kanban API (orchestrated by agent-service only)."""
from __future__ import annotations

import os
from typing import Any

import httpx

_DEFAULT_KANBAN = "http://kanban-api:8090"


def kanban_base_url() -> str:
    return os.environ.get("KANBAN_URL", _DEFAULT_KANBAN).rstrip("/")


async def fetch_projects() -> dict[str, Any]:
    url = f"{kanban_base_url()}/hub/projects"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def create_task(
    title: str,
    project: str,
    description: str = "",
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "title": title.strip(),
        "project": (project or "").strip(),
        "description": (description or "").strip(),
    }
    url = f"{kanban_base_url()}/tasks"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        return resp.json()
