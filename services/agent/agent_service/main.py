import logging

from fastapi import FastAPI

from .router import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
app = FastAPI(title="Clawvis Agent Service")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
