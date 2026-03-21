"""Pydantic models for the Kanban API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["Backlog", "To Start", "In Progress", "Blocked", "Review", "Done", "Archived"]
Priority = Literal["Critical", "High", "Medium", "Low"]
STATUSES: list[str] = ["Backlog", "To Start", "In Progress", "Blocked", "Review", "Done", "Archived"]


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    project: str = ""
    status: Status = "Backlog"
    priority: Priority = "Medium"
    effort_hours: float | None = None
    timeline: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    assignee: str = "DomBot"
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    progress: float = 0.0
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source_file: str = ""
    notes: str = ""
    created_by: str = "parser"
    created: str = ""
    updated: str = ""
    archived_at: str | None = None
    comments: list[dict] = Field(default_factory=list)


class TaskCreate(BaseModel):
    title: str
    project: str = ""
    priority: Priority = "Medium"
    effort_hours: float | None = None
    description: str = ""
    notes: str = ""
    timeline: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    assignee: str = "user"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class TaskUpdate(BaseModel):
    title: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    effort_hours: float | None = None
    description: str | None = None
    notes: str | None = None
    timeline: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    project: str | None = None
    assignee: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class CommentCreate(BaseModel):
    text: str
    author: str | None = None


class DependenciesUpdate(BaseModel):
    ids: list[str]


class SplitTaskRequest(BaseModel):
    count: int = Field(2, ge=1, le=20)
    base_title: str | None = None


class MetaUpdate(BaseModel):
    vision: str | None = None
    description: str | None = None
    pr_links: list[str] | None = None
