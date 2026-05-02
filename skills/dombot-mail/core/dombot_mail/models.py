from __future__ import annotations

from pydantic import BaseModel


class MailSummary(BaseModel):
    uid: str
    subject: str
    sender: str
    to: str
    date: str | None = None
    snippet: str = ""
    message_id: str | None = None


class MailDetail(MailSummary):
    cc: str | None = None
    text: str = ""
    html: str = ""


class ListResult(BaseModel):
    ok: bool
    folder: str
    messages: list[MailSummary]


class ReadResult(BaseModel):
    ok: bool
    message: MailDetail


class SimpleResult(BaseModel):
    ok: bool


class FoldersResult(BaseModel):
    ok: bool
    folders: list[str]


class ListAllResult(BaseModel):
    ok: bool
    by_folder: dict[str, ListResult]
