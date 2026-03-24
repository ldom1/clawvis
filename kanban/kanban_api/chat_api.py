"""Chat router — thin HTTP layer; logic lives in hub_core.chat_runtime."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from hub_core.chat_runtime import chat_stream, provider_status

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    system: str = (
        "You are the Clawvis assistant. You help the user manage their projects, "
        "tasks, and knowledge base. Be concise and actionable."
    )


@router.get("/hub/chat/status")
def chat_status():
    return provider_status()


@router.post("/hub/chat")
async def chat(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]

    async def generate():
        async for chunk in chat_stream(req.message, history, req.system):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
