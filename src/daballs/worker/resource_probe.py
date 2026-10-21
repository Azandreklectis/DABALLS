
import platform
import socket

import psutil

from daballs.controller.domain.worker import WorkerRegistration


def probe_resources(
    worker_id: str,
    offered_cpu_cores: int = 0,
    offered_memory_bytes: int = 0,
    display_name: str | None = None,
) -> WorkerRegistration:
    """Collect hardware information and configured resource offers."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return WorkerRegistration(
        worker_id=worker_id,
        display_name=display_name,
        hostname=socket.gethostname(),
        os_name=platform.system(),
        architecture=platform.machine(),
        cpu_logical_cores=psutil.cpu_count(logical=True) or 1,
        memory_total_bytes=memory.total,
        memory_available_bytes=memory.available,
        disk_total_bytes=disk.total,
        disk_free_bytes=disk.free,
        offered_cpu_cores=offered_cpu_cores,
        offered_memory_bytes=offered_memory_bytes,
    )
