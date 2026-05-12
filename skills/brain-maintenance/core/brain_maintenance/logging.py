"""Optional hooks for brain-maintenance (no external logger dependency)."""

from __future__ import annotations


def log_info(action: str, message: str, **meta: object) -> None:
    pass


def log_warning(action: str, message: str, **meta: object) -> None:
    pass


def log_error(action: str, message: str, **meta: object) -> None:
    pass
