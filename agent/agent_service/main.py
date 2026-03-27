# agent/agent_service/main.py
from fastapi import FastAPI

app = FastAPI(title="Clawvis Agent Service")


@app.get("/health")
def health():
    return {"status": "ok"}
