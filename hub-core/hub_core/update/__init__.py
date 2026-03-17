"""Update status and system metrics."""

from hub_core.update.status import main as status_main
from hub_core.update.system_metrics import main as system_metrics_main

__all__ = ["status_main", "system_metrics_main"]
