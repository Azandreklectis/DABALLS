from fastapi import APIRouter, HTTPException

from daballs.controller.domain.worker import (
    WorkerRecord,
    WorkerRegistration,
)
from daballs.controller.services.job_registry import job_registry
from daballs.controller.services.worker_registry import worker_registry

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])


def _reconcile_jobs() -> None:
    workers = worker_registry.list_workers()
    capacities = {
        worker.worker_id: (
            worker.offered_cpu_cores,
            worker.offered_memory_bytes,
        )
        for worker in workers
        if worker.status == "online"
    }
    job_registry.reconcile_workers(capacities)


@router.post("/register", response_model=WorkerRecord)
def register_worker(registration: WorkerRegistration) -> WorkerRecord:
    """Register a worker with the controller."""
    record = worker_registry.register(registration)
    _reconcile_jobs()
    return record


@router.get("", response_model=list[WorkerRecord])
def list_workers() -> list[WorkerRecord]:
    """List workers and reconcile jobs assigned to stale workers."""
    workers = worker_registry.list_workers()
    capacities = {
        worker.worker_id: (
            worker.offered_cpu_cores,
            worker.offered_memory_bytes,
        )
        for worker in workers
        if worker.status == "online"
    }
    job_registry.reconcile_workers(capacities)
    return workers


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
