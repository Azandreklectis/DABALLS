
import asyncio
import hmac
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from daballs.controller.api.v1.artifacts import router as artifacts_router
from daballs.controller.api.v1.jobs import router as jobs_router
from daballs.controller.api.v1.workers import router as workers_router
from daballs.controller.services.worker_monitor import (
    monitor_worker_lifecycle,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the background worker monitor's lifecycle."""
    stop_event = asyncio.Event()
    monitor_task = asyncio.create_task(
        monitor_worker_lifecycle(stop_event)
    )

    try:
        yield
    finally:
        stop_event.set()
        await monitor_task


app = FastAPI(
    title="DABALLS Controller",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def require_api_token(request: Request, call_next):
    """Protect API routes when DABALLS_API_TOKEN is configured.

    An unset token permits local development. Deployments exposed to other
    machines should configure a strong random token before starting.
    """
    expected = os.environ.get("DABALLS_API_TOKEN")
    if expected and request.url.path.startswith("/api/"):
        authorization = request.headers.get("Authorization", "")
        supplied = authorization.removeprefix("Bearer ").strip()
        if (
            not authorization.startswith("Bearer ")
            or not hmac.compare_digest(supplied, expected)
        ):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid bearer token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
    return await call_next(request)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the DABALLS controller is responding."""
    return {
        "status": "ok",
        "service": "daballs-controller",
        "version": "0.1.0",
    }


app.include_router(workers_router)
app.include_router(jobs_router)
app.include_router(artifacts_router)