"""Monitor worker heartbeats and clean up expired offline workers."""

import asyncio
import os

from daballs.controller.services.job_registry import job_registry
from daballs.controller.services.worker_registry import worker_registry


async def monitor_worker_lifecycle(
    stop_event: asyncio.Event,
    interval_seconds: float = 5.0,
    stale_after_seconds: float = 30.0,
    offline_retention_seconds: float | None = None,
) -> None:
    """Mark stale workers offline and remove them after the retention period."""
    if interval_seconds <= 0:
        raise ValueError("Monitor interval must be positive")

    if stale_after_seconds <= 0:
        raise ValueError("Stale timeout must be positive")

    if offline_retention_seconds is None:
        offline_retention_seconds = float(
            os.environ.get("DABALLS_OFFLINE_WORKER_RETENTION_SECONDS", "60")
        )

    if offline_retention_seconds <= 0:
        raise ValueError("Offline worker retention must be positive")

    while not stop_event.is_set():
        worker_registry.mark_stale_workers(
            stale_after_seconds=stale_after_seconds,
        )

        workers = worker_registry.list_workers()
        online_capacities = {
            worker.worker_id: (
                worker.offered_cpu_cores,
                worker.offered_memory_bytes,
            )
            for worker in workers
            if worker.status == "online"
        }

        # Reconcile jobs before removing their former worker records.
        job_registry.reconcile_workers(online_capacities)
        protected_worker_ids = {
            job.worker_id
            for job in job_registry.list_jobs()
            if job.worker_id is not None
            and job.status in ("queued", "running")
        }

        worker_registry.remove_expired_offline_workers(
            retention_seconds=offline_retention_seconds,
            protected_worker_ids=protected_worker_ids,
        )

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=interval_seconds,
            )
        except TimeoutError:
            pass
