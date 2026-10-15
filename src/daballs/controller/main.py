
from fastapi import FastAPI

from daballs.controller.api.v1.workers import router as workers_router

app = FastAPI(
    title="DABALLS Controller",
    version="0.1.0",
)

app.include_router(workers_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the DABALLS controller is responding."""
    return {
        "status": "ok",
        "service": "daballs-controller",
        "version": "0.1.0",
    }
