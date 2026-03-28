"""FastAPI app: Kanban + Logs API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .logs_api import router as logs_router
from .sse import router as sse_router

app = FastAPI(title="Kanban & Logs API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.include_router(router)
app.include_router(logs_router)
app.include_router(sse_router)
