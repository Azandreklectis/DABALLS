
import argparse
import logging
from threading import Event

import httpx

from daballs.controller.domain.worker import WorkerRecord
from daballs.worker.controller_client import (
    claim_next_job,
    register_with_controller,
    report_job_result,
    send_heartbeat,
)
from daballs.worker.identity import get_or_create_worker_id
from daballs.worker.job_executor import execute_job
from daballs.worker.resource_probe import probe_resources

logger = logging.getLogger(__name__)


def run_agent(
    worker_id: str,
    controller_url: str,
    offered_cpu_cores: int = 0,
    offered_memory_bytes: int = 0,
    display_name: str | None = None,
) -> WorkerRecord:
    """Probe resources and register this worker with the controller."""
    registration = probe_resources(
        worker_id,
        offered_cpu_cores=offered_cpu_cores,
        offered_memory_bytes=offered_memory_bytes,
        display_name=display_name,
    )

    return register_with_controller(registration, controller_url)

def process_one_job(
    worker_id: str,
    controller_url: str,
) -> None:
    """Claim, execute, and report one job if the queue has work."""
    job = claim_next_job(worker_id, controller_url)

    if job is None:
        return

    logger.info("Claimed job %s", job.job_id)

    try:
        result = execute_job(job)
    except Exception as exc:
        error = str(exc)[:1000] or "Job execution failed"
        logger.exception("Job %s failed", job.job_id)

        updated = report_job_result(
            job.job_id,
            controller_url,
            worker_id=worker_id,
            error=error,
        )
    else:
        updated = report_job_result(
            job.job_id,
            controller_url,
            worker_id=worker_id,
            result=result,
        )

    logger.info(
        "Job %s finished with status %s",
        updated.job_id,
        updated.status,
    )

def run_forever(
    worker_id: str,
    controller_url: str,
    heartbeat_interval: float = 10.0,
    stop_event: Event | None = None,
    offered_cpu_cores: int = 0,
    offered_memory_bytes: int = 0,
    display_name: str | None = None,
) -> None:
    """Register a worker and keep it alive with periodic heartbeats."""
    if heartbeat_interval <= 0:
        raise ValueError("Heartbeat interval must be positive")

    event = stop_event if stop_event is not None else Event()

    record = run_agent(
        worker_id,
        controller_url,
        offered_cpu_cores=offered_cpu_cores,
        offered_memory_bytes=offered_memory_bytes,
        display_name=display_name,
    )
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
                    record = run_agent(
                        worker_id,
                        controller_url,
                        offered_cpu_cores=offered_cpu_cores,
                        offered_memory_bytes=offered_memory_bytes,
                        display_name=display_name,
                    )
                    logger.info(
                        "Worker %s registered again",
                        record.worker_id,
                    )
                except httpx.HTTPError as registration_error:
                    logger.warning(
                        "Re-registration failed: %s",
                        registration_error,
                    )

            else:
                logger.warning("Heartbeat rejected: %s", exc)

        except httpx.HTTPError as exc:
            logger.warning("Heartbeat request failed: %s", exc)

        if not event.is_set():
            try:
                process_one_job(worker_id, controller_url)
            except httpx.HTTPError as exc:
                logger.warning("Job request failed: %s", exc)

def main() -> None:
    """Read command-line options and run the worker agent."""
    parser = argparse.ArgumentParser(
        description="Register this computer with the DABALLS controller."
    )

    parser.add_argument(
        "--worker-id",
        default=None,
        help="Worker ID. If omitted, use the persistent local identity.",
    )

    parser.add_argument(
        "--display-name",
        default=None,
        help="Human-readable name for this worker.",
    )

    parser.add_argument(
        "--controller-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the DABALLS controller.",
    )

    parser.add_argument(
        "--offer-cpu-cores",
        type=int,
        default=0,
        help="Number of logical CPU cores to offer (default: 0)",
    )

    parser.add_argument(
        "--offer-memory-mib",
        type=int,
        default=0,
        help="RAM to offer in MiB (default: 0)",
    )

    args = parser.parse_args()

    if args.offer_cpu_cores < 0 or args.offer_memory_mib < 0:
        parser.error("Resource offers cannot be negative")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    worker_id = args.worker_id or get_or_create_worker_id()

    try:
        run_forever(
            worker_id=worker_id,
            controller_url=args.controller_url,
            offered_cpu_cores=args.offer_cpu_cores,
            offered_memory_bytes=args.offer_memory_mib * 1024**2,
            display_name=args.display_name,
        )
    except KeyboardInterrupt:
        logger.info("Worker agent stopped")




if __name__ == "__main__":
    main()