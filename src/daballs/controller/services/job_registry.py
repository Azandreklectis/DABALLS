
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from daballs.controller.domain.job import JobRecord, JobSubmission


class JobRegistry:
    """Store jobs and coordinate their state transitions in memory."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def submit(self, submission: JobSubmission) -> JobRecord:
        record = JobRecord(**submission.model_dump())

        with self._lock:
            self._jobs[record.job_id] = record

        return record

    def list_jobs(self) -> list[JobRecord]:
        with self._lock:
            return list(self._jobs.values())

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def claim_next(self, worker_id: str) -> JobRecord | None:
        """Atomically claim the oldest queued job assigned to this worker."""
        with self._lock:
            for job_id, job in self._jobs.items():
                if job.worker_id == worker_id and job.status == "queued":
                    updated = job.model_copy(
                        update={
                            "status": "running",
                            "updated_at": datetime.now(UTC),
                        }
                    )
                    self._jobs[job_id] = updated
                    return updated

        return None

    def report_result(
        self,
        job_id: str,
        worker_id: str,
        result: int | None = None,
        result_data: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> JobRecord | None:
        """Record a result or failure from the worker assigned to a running job."""
        with self._lock:
            job = self._jobs.get(job_id)

            if job is None:
                return None

            if job.worker_id != worker_id:
                raise PermissionError(
                    "Only the assigned worker can report this job's result"
                )

            if job.status != "running":
                raise ValueError("Only running jobs can receive a result")

            supplied = sum(
                value is not None for value in (result, result_data, error)
            )
            if supplied != 1:
                raise ValueError(
                    "Provide exactly one of result, result_data, or error"
                )

            updated = job.model_copy(
                update={
                    "status": "failed" if error is not None else "completed",
                    "result": result,
                    "result_data": result_data,
                    "error": error,
                    "updated_at": datetime.now(UTC),
                }
            )
            self._jobs[job_id] = updated
            return updated

    def clear(self) -> None:
        """Clear all jobs; intended for tests and local development."""
        with self._lock:
            self._jobs.clear()


job_registry = JobRegistry()