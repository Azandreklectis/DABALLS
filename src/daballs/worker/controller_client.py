
import httpx

from daballs.controller.domain.job import (
    JobRecord,
    JobResultSubmission,
)
from daballs.controller.domain.worker import (
    WorkerRecord,
    WorkerRegistration,
)


def register_with_controller(
    registration: WorkerRegistration,
    controller_url: str,
) -> WorkerRecord:
    """Send worker registration data to the DABALLS controller."""
    url = (
        f"{controller_url.rstrip('/')}"
        "/api/v1/workers/register"
    )

    response = httpx.post(
        url,
        json=registration.model_dump(mode="json"),
        timeout=5.0,
    )
    response.raise_for_status()

    return WorkerRecord.model_validate(response.json())


def send_heartbeat(
    worker_id: str,
    controller_url: str,
) -> WorkerRecord:
    """Tell the controller that this worker is still reachable."""
    url = (
        f"{controller_url.rstrip('/')}"
        f"/api/v1/workers/{worker_id}/heartbeat"
    )

    response = httpx.post(url, timeout=5.0)
    response.raise_for_status()

    return WorkerRecord.model_validate(response.json())


def claim_next_job(
    worker_id: str,
    controller_url: str,
) -> JobRecord | None:
    """Claim the next queued job assigned to this worker."""
    url = f"{controller_url.rstrip('/')}/api/v1/jobs/next"

    response = httpx.post(
        url,
        params={"worker_id": worker_id},
        timeout=5.0,
    )
    response.raise_for_status()

    data = response.json()
    if data is None:
        return None

    return JobRecord.model_validate(data)


def report_job_result(
    job_id: str,
    controller_url: str,
    *,
    worker_id: str,
    result: int | None = None,
    result_data: dict | None = None,
    error: str | None = None,
) -> JobRecord:
    """Report a result or execution failure for the assigned worker."""
    url = (
        f"{controller_url.rstrip('/')}"
        f"/api/v1/jobs/{job_id}/result"
    )

    submission = JobResultSubmission(
        worker_id=worker_id,
        result=result,
        result_data=result_data,
        error=error[:1000] if error is not None else None,
    )

    response = httpx.post(
        url,
        json=submission.model_dump(mode="json"),
        timeout=5.0,
    )
    response.raise_for_status()

    return JobRecord.model_validate(response.json())