from __future__ import annotations

import email
import imaplib
import os
import shlex
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Tuple

from dombot_mail.config import MailSettings
from dombot_mail.models import (
    FoldersResult,
    ListAllResult,
    ListResult,
    MailDetail,
    MailSummary,
    ReadResult,
    SimpleResult,
)


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
    from dombot_logger import get_logger

    log = get_logger(process="skill:dombot-mail", model="")
except ImportError:
    from loguru import logger as _loguru
    class _LogAdapter:
        def info(self, action: str, message: str, **_: object) -> None:
            _loguru.info(f"[{action}] {message}")
        def error(self, action: str, message: str, **_: object) -> None:
            _loguru.error(f"[{action}] {message}")
        def warning(self, action: str, message: str, **_: object) -> None:
            _loguru.warning(f"[{action}] {message}")
    log = _LogAdapter()



def open_imap(settings: MailSettings, folder: str) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    imap.login(settings.user, settings.password)
    typ, _ = imap.select(folder)
    if typ != "OK":
        raise RuntimeError(f"Unable to select folder {folder}")
    return imap


def open_smtp(settings: MailSettings) -> smtplib.SMTP:
    if settings.smtp_port == 465:
        server = smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, context=ssl.create_default_context()
        )
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls(context=ssl.create_default_context())
    server.login(settings.user, settings.password)
    return server


def clean_header(raw: str | None) -> str:
    if not raw:
        return ""
    decoded = email.header.decode_header(raw)
    parts: List[str] = []
    for value, charset in decoded:
        if isinstance(value, bytes):
            parts.append(value.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(str(value))
    return "".join(parts).strip()


def extract_text_parts(msg: email.message.Message) -> Dict[str, str]:
    text = ""
    html = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get("Content-Disposition", "")
            if disp and "attachment" in disp.lower():
                continue
            payload = part.get_payload(decode=True) or b""
            if ctype == "text/plain" and not text:
                text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            elif ctype == "text/html" and not html:
                html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True) or b""
        text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

    if len(text) > 8000:
        text = text[:8000] + "\n...[truncated]..."
    if len(html) > 8000:
        html = html[:8000] + "\n...[truncated]..."
    return {"text": text, "html": html}


def parse_message(uid: bytes, msg: email.message.Message) -> MailDetail:
    parts = extract_text_parts(msg)
    snippet = (parts["text"] or parts["html"]).strip().replace("\r", " ").replace("\n", " ")
    if len(snippet) > 200:
        snippet = snippet[:200] + "..."
    return MailDetail(
        uid=uid.decode(),
        subject=clean_header(msg.get("Subject")),
        sender=clean_header(msg.get("From")),
        to=clean_header(msg.get("To")),
        cc=clean_header(msg.get("Cc")) or None,
        date=clean_header(msg.get("Date")) or None,
        snippet=snippet,
        message_id=msg.get("Message-ID") or None,
        text=parts["text"],
        html=parts["html"],
    )


def build_email(
    settings: MailSettings,
    to: str,
    cc: str,
    bcc: str,
    subject: str,
    text: str,
    html: str | None,
    reply: email.message.Message | None = None,
) -> Tuple[EmailMessage, List[str]]:
    msg = EmailMessage()
    msg["From"] = settings.user
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if subject:
        msg["Subject"] = subject

    if reply is not None:
        orig_mid = reply.get("Message-ID")
        refs = reply.get("References", "")
        subj = clean_header(reply.get("Subject", ""))
        if subj and not subj.lower().startswith("re:"):
            msg["Subject"] = f"Re: {subj}"
        if orig_mid:
            msg["In-Reply-To"] = orig_mid
            msg["References"] = (refs + " " + orig_mid).strip() if refs else orig_mid
        if not to:
            to_hdr = reply.get("Reply-To") or reply.get("From") or ""
            msg["To"] = clean_header(to_hdr)

    if html:
        msg.set_content(text or "")
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(text or "")

    recipients: List[str] = []
    for field in ("To", "Cc", "Bcc"):
        val = msg.get(field)
        if val:
            for part in str(val).split(","):
                addr = part.strip()
                if addr:
                    recipients.append(addr)
    if "Bcc" in msg:
        del msg["Bcc"]
    return msg, recipients


def list_all_input_folders(settings: MailSettings, limit_per_folder: int = 10) -> ListAllResult:
    by_folder: Dict[str, ListResult] = {}
    for folder in settings.input_folders:
        try:
            by_folder[folder] = list_messages(settings, folder, limit_per_folder)
        except Exception as e:
            log.warning("mail.list_all", f"Skip {folder}: {e}")
            by_folder[folder] = ListResult(ok=False, folder=folder, messages=[])
    return ListAllResult(ok=True, by_folder=by_folder)


def list_messages(settings: MailSettings, folder: str, limit: int) -> ListResult:
    log.info("mail.list", f"Listing last {limit} messages in {folder}")
    imap = open_imap(settings, folder)
    try:
        try:
            typ, data = imap.uid("search", None, "ALL")
            if typ != "OK" or not data or not data[0]:
                return ListResult(ok=True, folder=folder, messages=[])
            uids = data[0].split()[-limit:]
            messages: List[MailSummary] = []
            for uid in reversed(uids):
                typ, fetched = imap.uid("fetch", uid, "(RFC822 FLAGS)")
                if typ != "OK" or not fetched or not fetched[0]:
                    continue
                raw = fetched[0][1]
                msg = email.message_from_bytes(raw)
                detail = parse_message(uid, msg)
                messages.append(MailSummary.model_validate(detail))
            return ListResult(ok=True, folder=folder, messages=messages)
        except Exception as e:
            log.error("mail.list", str(e))
            raise
    finally:
        try:
            imap.logout()
        except Exception as exc:
            log.warning("mail.list", f"Failed to logout IMAP: {exc}")


def read_message(settings: MailSettings, folder: str, uid: str) -> ReadResult:
    log.info("mail.read", f"Reading message {uid} from {folder}")
    imap = open_imap(settings, folder)
    try:
        try:
            typ, fetched = imap.uid("fetch", uid.encode(), "(RFC822)")
            if typ != "OK" or not fetched or not fetched[0]:
                raise RuntimeError("Message not found")
            raw = fetched[0][1]
            msg = email.message_from_bytes(raw)
            return ReadResult(ok=True, message=parse_message(uid.encode(), msg))
        except Exception as e:
            log.error("mail.read", str(e))
            raise
    finally:
        try:
            imap.logout()
        except Exception as exc:
            log.warning("mail.read", f"Failed to logout IMAP: {exc}")


def send_message(
    settings: MailSettings, to: str, cc: str, bcc: str, subject: str, text: str, html: str | None
) -> SimpleResult:
    if not to:
        raise RuntimeError("Missing recipient address")
    log.info("mail.send", f"Sending email to {to} with subject: {subject}")
    msg, recipients = build_email(settings, to, cc, bcc, subject, text, html)
    server = open_smtp(settings)
    try:
        try:
            server.send_message(msg, from_addr=settings.user, to_addrs=recipients)
        except Exception as e:
            log.error("mail.send", str(e))
            raise
    finally:
        try:
            server.quit()
        except Exception as exc:
            log.warning("mail.send", f"Failed to quit SMTP: {exc}")
    return SimpleResult(ok=True)


def reply_message(
    settings: MailSettings,
    folder: str,
    uid: str,
    to: str,
    cc: str,
    bcc: str,
    text: str,
    html: str | None,
) -> SimpleResult:
    log.info("mail.reply", f"Replying to message {uid} in {folder}")
    imap = open_imap(settings, folder)
    try:
        try:
            typ, fetched = imap.uid("fetch", uid.encode(), "(RFC822)")
            if typ != "OK" or not fetched or not fetched[0]:
                raise RuntimeError("Original message not found")
            raw = fetched[0][1]
            orig = email.message_from_bytes(raw)
        except Exception as e:
            log.error("mail.reply", str(e))
            raise
    finally:
        try:
            imap.logout()
        except Exception as exc:
            log.warning("mail.reply", f"Failed to logout IMAP: {exc}")

    msg, recipients = build_email(settings, to, cc, bcc, "", text, html, orig)
    server = open_smtp(settings)
    try:
        try:
            server.send_message(msg, from_addr=settings.user, to_addrs=recipients)
        except Exception as e:
            log.error("mail.reply", str(e))
            raise
    finally:
        try:
            server.quit()
        except Exception as exc:
            log.warning("mail.reply", f"Failed to quit SMTP: {exc}")
    return SimpleResult(ok=True)


def archive_message(settings: MailSettings, folder: str, uid: str) -> SimpleResult:
    log.info("mail.archive", f"Archiving message {uid} from {folder} to {settings.archive_folder}")
    imap = open_imap(settings, folder)
    try:
        try:
            typ, _ = imap.uid("COPY", uid.encode(), settings.archive_folder)
            if typ != "OK":
                raise RuntimeError("Archive COPY failed")
            typ, _ = imap.uid("STORE", uid.encode(), "+FLAGS.SILENT", r"(\Deleted)")
            if typ != "OK":
                raise RuntimeError("Archive STORE failed")
            imap.expunge()
        except Exception as e:
            log.error("mail.archive", str(e))
            raise
    finally:
        try:
            imap.logout()
        except Exception as exc:
            log.warning("mail.archive", f"Failed to logout IMAP: {exc}")
    return SimpleResult(ok=True)


def list_folders(settings: MailSettings) -> FoldersResult:
    log.info("mail.folders", "Listing IMAP folders")
    imap = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
    imap.login(settings.user, settings.password)
    try:
        try:
            typ, data = imap.list()
            if typ != "OK" or not data:
                return FoldersResult(ok=False, folders=[])
            folders: List[str] = []
            for line in data:
                decoded = line.decode("utf-8", errors="replace")
                try:
                    tokens = shlex.split(decoded)
                    name = tokens[-1] if tokens else decoded.strip()
                except ValueError:
                    name = decoded.strip()
                if name and name not in ("/", "."):
                    folders.append(name)
            return FoldersResult(ok=True, folders=folders)
        except Exception as e:
            log.error("mail.folders", str(e))
            raise
    finally:
        try:
            imap.logout()
        except Exception as exc:
            log.warning("mail.folders", f"Failed to logout IMAP: {exc}")


class Service:
    def __init__(self, settings: MailSettings | None = None) -> None:
        self.settings = settings or MailSettings.from_env()

    def list_input_folders(self, limit_per_folder: int = 10) -> ListAllResult:
        return list_all_input_folders(self.settings, limit_per_folder)

    def list(self, folder: str, limit: int) -> ListResult:
        return list_messages(self.settings, folder, limit)

    def read(self, folder: str, uid: str) -> ReadResult:
        return read_message(self.settings, folder, uid)

    def send(
        self, to: str, cc: str, bcc: str, subject: str, text: str, html: str | None
    ) -> SimpleResult:
        return send_message(self.settings, to, cc, bcc, subject, text, html)

    def reply(
        self, folder: str, uid: str, to: str, cc: str, bcc: str, text: str, html: str | None
    ) -> SimpleResult:
        return reply_message(self.settings, folder, uid, to, cc, bcc, text, html)

    def folders(self) -> FoldersResult:
        return list_folders(self.settings)

    def archive(self, folder: str, uid: str) -> SimpleResult:
        return archive_message(self.settings, folder, uid)
