
import argparse
import logging
from threading import Event

import httpx

from daballs.worker.controller_client import send_heartbeat

from daballs.controller.domain.worker import WorkerRecord
from daballs.worker.controller_client import register_with_controller
from daballs.worker.identity import get_or_create_worker_id
from daballs.worker.resource_probe import probe_resources


def run_agent(worker_id: str, controller_url: str) -> WorkerRecord:
    """Detect local resources and register this worker with the controller."""
    registration = probe_resources(worker_id)
    return register_with_controller(registration, controller_url)


def main() -> None:
    """Read command-line options and run the worker registration process."""
    parser = argparse.ArgumentParser(
        description="Register this computer with the DABALLS controller."
    )
    parser.add_argument(
        "--worker-id",
        default=None,
        help="Worker ID. If omitted, use the persistent local identity.",
    )
    parser.add_argument(
        "--controller-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the DABALLS controller.",
    )
    args = parser.parse_args()

    worker_id = args.worker_id or get_or_create_worker_id()
    record = run_agent(worker_id, args.controller_url)
    print(record.model_dump_json(indent=2))


logger = logging.getLogger(__name__)


def run_forever(
    worker_id: str,
    controller_url: str,
    heartbeat_interval: float = 10.0,
    stop_event: Event | None = None,
) -> None:
    """Register a worker and keep it alive with periodic heartbeats."""
    if heartbeat_interval <= 0:
        raise ValueError("Heartbeat interval must be positive")

    event = stop_event if stop_event is not None else Event()

    record = run_agent(worker_id, controller_url)
    logger.info("Worker %s registered with controller", record.worker_id)

    while not event.wait(heartbeat_interval):
        try:
            record = send_heartbeat(worker_id, controller_url)
            logger.info("Heartbeat acknowledged for %s", record.worker_id)

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.warning(
                    "Worker %s is unknown to the controller; registering again",
                    worker_id,
                )
                try:
                    record = run_agent(worker_id, controller_url)
                    logger.info("Worker %s registered again", record.worker_id)
                except httpx.HTTPError as registration_error:
                    logger.warning(
                        "Re-registration failed: %s",
                        registration_error,
                    )
            else:
                logger.warning("Heartbeat rejected: %s", exc)

        except httpx.HTTPError as exc:
            logger.warning("Heartbeat request failed: %s", exc)


if __name__ == "__main__":
    main()