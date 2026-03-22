"""Entry point: python -m brain_maintenance [trim|recalibrate|recover]."""

from __future__ import annotations

import sys

from brain_maintenance.recalibrate import main as recalibrate_main
from brain_maintenance.recover import main as recover_main
from brain_maintenance.trim import main as trim_main


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "trim"
    if cmd == "trim":
        return trim_main()
    if cmd == "recalibrate":
        recalibrate_main()
        return 0
    if cmd == "recover":
        return recover_main()
    print("Usage: python -m brain_maintenance {trim|recalibrate|recover}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
