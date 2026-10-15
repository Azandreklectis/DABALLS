
from fastapi import APIRouter, HTTPException, Query, status

from daballs.controller.domain.job import (
    JobRecord,
    JobResultSubmission,
    JobSubmission,
)
from daballs.controller.services.job_registry import job_registry
from daballs.controller.services.worker_registry import worker_registry

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=JobRecord,
    status_code=status.HTTP_201_CREATED,
)
def submit_job(submission: JobSubmission) -> JobRecord:
    workers = worker_registry.list_workers()
    worker = next(
        (item for item in workers if item.worker_id == submission.worker_id),
        None,
    )

    if worker is None:
        raise HTTPException(status_code=404, detail="Worker is not registered")

    if worker.status != "online":
        raise HTTPException(status_code=409, detail="Worker is offline")

    return job_registry.submit(submission)


@router.get("", response_model=list[JobRecord])
def list_jobs() -> list[JobRecord]:
    return job_registry.list_jobs()


@router.post("/next", response_model=JobRecord | None)
def claim_next_job(
    worker_id: str = Query(min_length=1, max_length=128),
) -> JobRecord | None:
    workers = worker_registry.list_workers()
    worker = next(
        (item for item in workers if item.worker_id == worker_id),
        None,
    )

    if worker is None:
        raise HTTPException(status_code=404, detail="Worker is not registered")

    if worker.status != "online":
        raise HTTPException(status_code=409, detail="Worker is offline")

    return job_registry.claim_next(worker_id)


@router.get("/{job_id}", response_model=JobRecord)
def get_job(job_id: str) -> JobRecord:
    job = job_registry.get(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/{job_id}/result", response_model=JobRecord)
def report_job_result(
    job_id: str,
    submission: JobResultSubmission,
) -> JobRecord:
    try:
        job = job_registry.report_result(
            job_id,
            result=submission.result,
            error=submission.error,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job