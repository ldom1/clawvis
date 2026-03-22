"""Entry point: python -m knowledge_consolidator [session_type]."""

from __future__ import annotations

import sys
from datetime import datetime

from knowledge_consolidator.curiosity import CuriosityAgent

VALID_SESSIONS = (
    "mail",
    "tech",
    "geopolitics",
    "culture",
    "community",
    "latest",
    "tech_news",
)


def main() -> None:
    if len(sys.argv) > 1:
        session_type = sys.argv[1]
    else:
        hour = datetime.now().hour
        session_type = (
            "tech" if hour in range(6, 11) else
            "geopolitics" if hour in range(11, 15) else
            "culture" if hour in range(15, 19) else
            "community" if hour in range(19, 23) else
            "tech"
        )
    if session_type not in VALID_SESSIONS:
        print(f"❌ Unknown session type: {session_type}")
        print("Valid:", ", ".join(VALID_SESSIONS))
        sys.exit(1)
    CuriosityAgent(session_type).run()


if __name__ == "__main__":
    main()
