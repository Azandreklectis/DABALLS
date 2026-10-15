
from fastapi import APIRouter, HTTPException

from daballs.controller.domain.worker import (
    WorkerRecord,
    WorkerRegistration,
)
from daballs.controller.services.worker_registry import worker_registry

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])


@router.post("/register", response_model=WorkerRecord)
def register_worker(registration: WorkerRegistration) -> WorkerRecord:
    """Register a worker with the controller."""
    return worker_registry.register(registration)


@router.get("", response_model=list[WorkerRecord])
def list_workers() -> list[WorkerRecord]:
    """List workers currently known to the controller."""
    return worker_registry.list_workers()

@router.post("/{worker_id}/heartbeat", response_model=WorkerRecord)
def heartbeat_worker(worker_id: str) -> WorkerRecord:
    """Record a heartbeat from a registered worker."""
    record = worker_registry.heartbeat(worker_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Worker is not registered",
        )

    return record
