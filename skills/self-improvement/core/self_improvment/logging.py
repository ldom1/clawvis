"""Optional DomBot logger integration (skills/logger/core under CLAWVIS_ROOT)."""

from __future__ import annotations

import sys

from self_improvment.config import LOGGER_PACKAGE_CORE_PATH

_logger_core = LOGGER_PACKAGE_CORE_PATH
if _logger_core is not None and _logger_core.is_dir() and str(_logger_core) not in sys.path:
    sys.path.insert(0, str(_logger_core))

try:
    from dombot_logger import get_logger  # type: ignore[import-not-found]

    _LOG = get_logger(process="cron:self-improvement", model="")  # pylint: disable=invalid-name
except ImportError:
    _LOG = None  # pylint: disable=invalid-name


def log_info(action: str, message: str, **meta: object) -> None:
    if _LOG:
        _LOG.info(action, message, **meta)


def log_error(action: str, message: str, **meta: object) -> None:
    if _LOG:
        _LOG.error(action, message, **meta)


def log_warning(action: str, message: str, **meta: object) -> None:
    if _LOG:
        _LOG.warning(action, message, **meta)
