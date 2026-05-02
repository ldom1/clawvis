"""DomBot logger integration (${CLAWVIS_ROOT}/skills/logger/core)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _logger_core() -> Path | None:
    r = os.environ.get("CLAWVIS_ROOT", "").strip()
    if r:
        p = Path(r).expanduser().resolve() / "skills" / "logger" / "core"
        if p.is_dir():
            return p
    for b in (Path.home() / "lab" / "clawvis", Path.home() / "Lab" / "clawvis"):
        p = b / "skills" / "logger" / "core"
        if p.is_dir():
            return p
    return None


_lc = _logger_core()
if _lc is not None and str(_lc) not in sys.path:
    sys.path.insert(0, str(_lc))

try:
    from dombot_logger import get_logger  # type: ignore[import-not-found]

    _LOG = get_logger(process="cron:brain-maintenance", model="")  # pylint: disable=invalid-name
except ImportError:
    _LOG = None  # pylint: disable=invalid-name


def log_info(action: str, message: str, **meta: object) -> None:
    if _LOG:
        _LOG.info(action, message, **meta)


def log_warning(action: str, message: str, **meta: object) -> None:
    if _LOG:
        _LOG.warning(action, message, **meta)


def log_error(action: str, message: str, **meta: object) -> None:
    if _LOG:
        _LOG.error(action, message, **meta)
