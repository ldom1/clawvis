#!/usr/bin/env python3
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from kanban_api.api import router as kanban_router
from kanban_api.logs_api import router as logs_router
from kanban_api.sse import router as sse_router

HUB_PUBLIC_DIR = Path(__file__).resolve().parents[1] / "hub" / "public"
app = FastAPI(title="Clawvis Dev Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(kanban_router, prefix="/api/kanban")
app.include_router(logs_router, prefix="/api/kanban")
app.include_router(sse_router, prefix="/api/kanban")
app.mount("/", StaticFiles(directory=str(HUB_PUBLIC_DIR), html=True), name="hub")


def main() -> None:
    uvicorn.run("scripts.dev_server:app", host="0.0.0.0", port=8088, reload=True)


if __name__ == "__main__":
    main()
