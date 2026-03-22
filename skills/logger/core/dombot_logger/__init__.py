from .config import load_env

load_env()

from .logger import DomBotLogger, get_logger, log
from .models import LogEntry

__all__ = ["DomBotLogger", "get_logger", "log", "LogEntry"]


def cli_main():
    """CLI entrypoint: dombot-log LEVEL PROCESS MODEL ACTION MESSAGE [METADATA_JSON]"""
    import sys

    args = sys.argv[1:]
    if len(args) < 5:
        print("Usage: dombot-log LEVEL PROCESS MODEL ACTION MESSAGE [METADATA_JSON]")
        sys.exit(1)
    import json as _json

    level, process, model, action, message = args[:5]
    metadata = _json.loads(args[5]) if len(args) > 5 else {}
    log(
        level=level.upper(),
        process=process,
        model=model,
        action=action,
        message=message,
        metadata=metadata,
    )  # noqa: E501
