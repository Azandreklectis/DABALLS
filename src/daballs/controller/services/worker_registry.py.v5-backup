
from datetime import UTC, datetime

from daballs.controller.domain.worker import (
    WorkerRecord,
    WorkerRegistration,
)


class WorkerRegistry:
    """Maintain the workers known to this controller process."""

    def __init__(self) -> None:
        self._workers: dict[str, WorkerRecord] = {}

    def register(self, registration: WorkerRegistration) -> WorkerRecord:
        now = datetime.now(UTC)
        existing = self._workers.get(registration.worker_id)

        record = WorkerRecord(
            **registration.model_dump(),
            status="online",
            registered_at=existing.registered_at if existing else now,
            last_seen_at=now,
        )

        self._workers[record.worker_id] = record
        return record

    def list_workers(self) -> list[WorkerRecord]:
        self.mark_stale_workers()
        return list(self._workers.values())

    def clear(self) -> None:
        """Clear in-memory state, primarily for tests."""
        self._workers.clear()

    def heartbeat(self, worker_id: str) -> WorkerRecord | None:
        """Record a heartbeat from a known worker."""
        existing = self._workers.get(worker_id)

        if existing is None:
            return None

        updated = existing.model_copy(
            update={
                "last_seen_at": datetime.now(UTC),
                "status": "online",
            }
        )

        self._workers[worker_id] = updated
        return updated

    def mark_stale_workers(
        self,
        stale_after_seconds: float = 30.0,
        now: datetime | None = None,
    ) -> None:
        """Mark workers offline when their last heartbeat is too old."""
        if stale_after_seconds <= 0:
            raise ValueError("Stale timeout must be positive")

        current_time = now if now is not None else datetime.now(UTC)

        for worker_id, record in list(self._workers.items()):
            age_seconds = (
                current_time - record.last_seen_at
            ).total_seconds()

            if record.status == "online" and age_seconds > stale_after_seconds:
                self._workers[worker_id] = record.model_copy(
                    update={"status": "offline"}
                )


worker_registry = WorkerRegistry()
