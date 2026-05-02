from __future__ import annotations

import json
import sys

import typer

from dombot_mail.service import Service

app = typer.Typer()
svc = Service()


def _safe_run(fn, *args, **kwargs):
    """On exception: print {"ok": false, "error": "..."} and exit 0 so cron/skill run does not fail."""
    try:
        out = fn(*args, **kwargs)
        print(json.dumps(out.model_dump(), ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(0)


@app.command()
def list(
    folder: str = typer.Option(...),
    limit: int = 10,
) -> None:
    _safe_run(svc.list, folder, limit)


@app.command("list-inbox")
def list_inbox(limit_per_folder: int = typer.Option(10, "--limit")) -> None:
    """List messages from all input folders (INBOX, Promotions, SocialNetworks)."""
    _safe_run(svc.list_input_folders, limit_per_folder)


@app.command()
def read(
    folder: str = typer.Option(...),
    uid: str = typer.Option(...),
) -> None:
    _safe_run(svc.read, folder, uid)


@app.command()
def send(
    to: str = typer.Option(...),
    cc: str = "",
    bcc: str = "",
    subject: str = "",
    text: str = "",
    html: str | None = None,
) -> None:
    _safe_run(svc.send, to, cc, bcc, subject, text, html)


@app.command()
def reply(
    folder: str = typer.Option(...),
    uid: str = typer.Option(...),
    to: str = "",
    cc: str = "",
    bcc: str = "",
    text: str = "",
    html: str | None = None,
) -> None:
    _safe_run(svc.reply, folder, uid, to, cc, bcc, text, html)


@app.command()
def archive(
    folder: str = typer.Option(...),
    uid: str = typer.Option(...),
) -> None:
    _safe_run(svc.archive, folder, uid)


@app.command()
def folders() -> None:
    _safe_run(svc.folders)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
