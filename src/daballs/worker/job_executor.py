
from daballs.controller.domain.job import JobRecord


def execute_job(job: JobRecord) -> int:
    """Execute a supported job and return its integer result."""
    if job.workload_type == "sum_integers":
        return sum(job.input_data)

    raise ValueError(f"Unsupported workload type: {job.workload_type}")