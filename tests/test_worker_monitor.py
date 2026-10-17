
import asyncio

from daballs.controller.domain.worker import WorkerRegistration
from daballs.controller.services.worker_monitor import monitor_worker_lifecycle
from daballs.controller.services.worker_registry import WorkerRegistry


def test_monitor_marks_stale_worker_offline() -> None:
    async def scenario() -> None:
        registry = WorkerRegistry()
        registration = WorkerRegistration(
            worker_id="worker-stale",
            hostname="test-host",
            os_name="Linux",
            architecture="x86_64",
            cpu_logical_cores=8,
            memory_total_bytes=16 * 1024**3,
            memory_available_bytes=8 * 1024**3,
        )
        registry.register(registration)

        # Use a short timeout so the test doesn't wait 30 seconds.
        import daballs.controller.services.worker_monitor as monitor_module

        original_registry = monitor_module.worker_registry
        monitor_module.worker_registry = registry

        stop_event = asyncio.Event()
        task = asyncio.create_task(
            monitor_worker_lifecycle(
                stop_event,
                interval_seconds=0.01,
                stale_after_seconds=0.02,
            )
        )

        try:
            await asyncio.sleep(0.08)

            assert registry._workers["worker-stale"].status == "offline"
        finally:
            stop_event.set()
            await task
            monitor_module.worker_registry = original_registry

    asyncio.run(scenario())