from fastapi import APIRouter, HTTPException, Query, status

from daballs.controller.domain.job import (
    JobRecord,
    JobResultSubmission,
    JobSubmission,
)
from daballs.controller.services.job_registry import job_registry
from daballs.controller.services.worker_registry import worker_registry

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _online_worker_capacities() -> dict[str, tuple[int, int]]:
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
    return capacities


@router.post(
    "",
    response_model=JobRecord,
    status_code=status.HTTP_201_CREATED,
)
def submit_job(submission: JobSubmission) -> JobRecord:
    capacities = _online_worker_capacities()

    if submission.worker_id is not None:
        if submission.worker_id not in {
            worker.worker_id
            for worker in worker_registry.list_workers()
        }:
            raise HTTPException(status_code=404, detail="Worker is not registered")

        if submission.worker_id not in capacities:
            raise HTTPException(status_code=409, detail="Worker is offline")

    try:
        return job_registry.submit(submission, worker_capacities=capacities)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[JobRecord])
def list_jobs() -> list[JobRecord]:
    _online_worker_capacities()
    return job_registry.list_jobs()


@router.post("/next", response_model=JobRecord | None)
def claim_next_job(
    worker_id: str = Query(min_length=1, max_length=128),
) -> JobRecord | None:
    capacities = _online_worker_capacities()

    workers = worker_registry.list_workers()
    if not any(worker.worker_id == worker_id for worker in workers):
        raise HTTPException(status_code=404, detail="Worker is not registered")

    if worker_id not in capacities:
        raise HTTPException(status_code=409, detail="Worker is offline")

    return job_registry.claim_next(worker_id)


@router.get("/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> JobRecord:
    _online_worker_capacities()
    job = job_registry.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/{job_id}/result", response_model=JobRecord)
def report_job_result(
    job_id: str,
    submission: JobResultSubmission,
) -> JobRecord:
    _online_worker_capacities()

    try:
        job = job_registry.report_result(
            job_id,
            worker_id=submission.worker_id,
            result=submission.result,
            result_data=submission.result_data,
            error=submission.error,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
