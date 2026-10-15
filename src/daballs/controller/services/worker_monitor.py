
import asyncio

from daballs.controller.services.worker_registry import worker_registry


async def monitor_worker_lifecycle(
    stop_event: asyncio.Event,
    interval_seconds: float = 5.0,
    stale_after_seconds: float = 30.0,
) -> None:
    """Periodically mark workers offline when their heartbeats become stale."""
    if interval_seconds <= 0:
        raise ValueError("Monitor interval must be positive")

    if stale_after_seconds <= 0:
        raise ValueError("Stale timeout must be positive")

    while not stop_event.is_set():
        worker_registry.mark_stale_workers(
            stale_after_seconds=stale_after_seconds,
        )

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=interval_seconds,
            )
        except TimeoutError:
            pass