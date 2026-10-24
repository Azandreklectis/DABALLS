from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from daballs.controller.domain.job import JobRecord, JobSubmission
from daballs.controller.services.storage import SQLiteStateStore, get_database_path

ResourceCapacity = tuple[int, int]


class JobRegistry:
    """Store jobs and atomically account for their advertised resource capacity."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()
        self._store = SQLiteStateStore(database_path) if database_path is not None else None
        if self._store is not None:
            for serialized in self._store.load_records('jobs'):
                record = JobRecord.model_validate_json(serialized)
                if record.status == 'running':
                    record = record.model_copy(update={
                        'status': 'failed',
                        'error': 'Controller restarted while this job was running; automatic retry was avoided',
                        'updated_at': datetime.now(UTC),
                    })
                    self._store.save_record('jobs', record.job_id, record.model_dump_json())
                self._jobs[record.job_id] = record

    def _used_capacity(self, worker_id: str) -> ResourceCapacity:
        """Calculate capacity reserved by queued and running jobs.

        Caller must hold ``_lock``.
        """
        cpu_used = 0
        memory_used = 0

        for job in self._jobs.values():
            if (
                job.worker_id == worker_id
                and job.status in ("queued", "running")
            ):
                cpu_used += job.required_cpu_cores
                memory_used += job.required_memory_bytes

        return cpu_used, memory_used

    def submit(
        self,
        submission: JobSubmission,
        worker_capacities: Mapping[str, ResourceCapacity] | None = None,
    ) -> JobRecord:
        """Assign a worker and queue the job under one registry lock.

        ``worker_capacities`` contains online workers and their advertised
        (CPU cores, memory bytes). Omitting it preserves direct registry use
        by existing tests and internal callers that explicitly assign a worker.
        """
        with self._lock:
            capacities = worker_capacities
            requested_cpu = submission.required_cpu_cores
            requested_memory = submission.required_memory_bytes

            if submission.worker_id is not None:
                selected_worker = submission.worker_id

                if capacities is not None:
                    if selected_worker not in capacities:
                        raise ValueError("Selected worker is not online")

                    offered_cpu, offered_memory = capacities[selected_worker]
                    used_cpu, used_memory = self._used_capacity(selected_worker)

                    if (
                        used_cpu + requested_cpu > offered_cpu
                        or used_memory + requested_memory > offered_memory
                    ):
                        raise ValueError(
                            "Selected worker has insufficient unallocated "
                            "advertised capacity"
                        )
            else:
                if capacities is None:
                    raise ValueError(
                        "Online worker capacities are required for automatic scheduling"
                    )

                candidates: list[tuple[float, str]] = []

                for worker_id, (offered_cpu, offered_memory) in capacities.items():
                    used_cpu, used_memory = self._used_capacity(worker_id)

                    if (
                        used_cpu + requested_cpu > offered_cpu
                        or used_memory + requested_memory > offered_memory
                    ):
                        continue

                    # Prefer the worker with the lowest projected utilization.
                    cpu_utilization = (used_cpu + requested_cpu) / offered_cpu
                    memory_utilization = (
                        (used_memory + requested_memory) / offered_memory
                    )
                    score = cpu_utilization + memory_utilization
                    candidates.append((score, worker_id))

                if not candidates:
                    raise ValueError(
                        "No online worker has sufficient unallocated "
                        "advertised capacity"
                    )

                _, selected_worker = min(candidates)

            data = submission.model_dump()
            data["worker_id"] = selected_worker
            record = JobRecord(**data)
            self._jobs[record.job_id] = record
            self._persist(record)
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
                    self._persist(updated)
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
        """Record a result or failure from the assigned worker."""
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
            self._persist(updated)
            return updated

    def reconcile_workers(
        self,
        worker_capacities: Mapping[str, ResourceCapacity],
    ) -> None:
        """Recover jobs assigned to workers that are no longer online.

        Queued jobs are moved to another worker with enough advertised
        capacity. Running jobs are failed rather than automatically retried,
        because execution may have produced side effects before disconnecting.
        """
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                if job.status not in ("queued", "running"):
                    continue
                if job.worker_id in worker_capacities:
                    continue

                now = datetime.now(UTC)

                if job.status == "running":
                    self._jobs[job_id] = job.model_copy(
                        update={
                            "status": "failed",
                            "error": "Assigned worker went offline while the job was running",
                            "updated_at": now,
                        }
                    )
                    continue

                candidates: list[tuple[float, str]] = []

                for worker_id, (offered_cpu, offered_memory) in worker_capacities.items():
                    used_cpu, used_memory = self._used_capacity(worker_id)

                    if (
                        used_cpu + job.required_cpu_cores > offered_cpu
                        or used_memory + job.required_memory_bytes > offered_memory
                    ):
                        continue

                    cpu_score = (used_cpu + job.required_cpu_cores) / offered_cpu
                    memory_score = (
                        used_memory + job.required_memory_bytes
                    ) / offered_memory
                    candidates.append((cpu_score + memory_score, worker_id))

                if candidates:
                    _, selected_worker = min(candidates)
                    self._jobs[job_id] = job.model_copy(
                        update={
                            "worker_id": selected_worker,
                            "updated_at": now,
                        }
                    )
                else:
                    self._jobs[job_id] = job.model_copy(
                        update={
                            "status": "failed",
                            "error": (
                                "Assigned worker went offline and no online worker "
                                "has sufficient advertised capacity"
                            ),
                            "updated_at": now,
                        }
                    )

            if self._store is not None:
                for record in self._jobs.values():
                    self._persist(record)

    def _persist(self, record: JobRecord) -> None:
        if self._store is not None:
            self._store.save_record('jobs', record.job_id, record.model_dump_json())

    def clear(self) -> None:
        """Clear all jobs; intended for tests and local development."""
        with self._lock:
            self._jobs.clear()
            if self._store is not None:
                self._store.clear_records('jobs')


job_registry = JobRegistry(database_path=get_database_path())
