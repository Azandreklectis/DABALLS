
import platform
import socket

import psutil

from daballs.controller.domain.worker import WorkerRegistration


def probe_resources(worker_id: str) -> WorkerRegistration:
    """Collect the current machine's hardware and resource information."""
    memory = psutil.virtual_memory()

    return WorkerRegistration(
        worker_id=worker_id,
        hostname=socket.gethostname(),
        os_name=platform.system(),
        architecture=platform.machine(),
        cpu_logical_cores=psutil.cpu_count(logical=True) or 1,
        memory_total_bytes=memory.total,
        memory_available_bytes=memory.available,
    )
