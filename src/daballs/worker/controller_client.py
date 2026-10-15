"""uthaake resource is list curl karega"""
import httpx

from daballs.controller.domain.worker import WorkerRecord, WorkerRegistration


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