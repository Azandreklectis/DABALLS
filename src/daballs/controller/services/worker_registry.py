"""Thread-safe worker registry with optional SQLite persistence."""

from datetime import UTC, datetime
from pathlib import Path
from threading import RLock

from daballs.controller.domain.worker import WorkerRecord, WorkerRegistration
from daballs.controller.services.storage import SQLiteStateStore, get_database_path


class WorkerRegistry:
    """Maintain worker records and persist changes when configured."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self._workers: dict[str, WorkerRecord] = {}
        self._lock = RLock()
        self._store = SQLiteStateStore(database_path) if database_path is not None else None

        if self._store is not None:
            for serialized in self._store.load_records("workers"):
                record = WorkerRecord.model_validate_json(serialized)
                # Never assume a worker is connected after a controller restart.
                record = record.model_copy(update={"status": "offline"})
                self._workers[record.worker_id] = record
                self._persist(record)

    def _persist(self, record: WorkerRecord) -> None:
        if self._store is not None:
            self._store.save_record("workers", record.worker_id, record.model_dump_json())

    def register(self, registration: WorkerRegistration) -> WorkerRecord:
        with self._lock:
            now = datetime.now(UTC)
            existing = self._workers.get(registration.worker_id)
            record = WorkerRecord(
                **registration.model_dump(),
                status="online",
                registered_at=existing.registered_at if existing else now,
                last_seen_at=now,
            )
            self._workers[record.worker_id] = record
            self._persist(record)
            return record

    def list_workers(self) -> list[WorkerRecord]:
        with self._lock:
            self.mark_stale_workers()
            return list(self._workers.values())

    def remove_expired_offline_workers(
        self,
        retention_seconds: float = 60.0,
        now: datetime | None = None,
        protected_worker_ids: set[str] | None = None,
    ) -> list[str]:
        """Delete expired offline workers unless active jobs still reference them."""
        if retention_seconds <= 0:
            raise ValueError("Offline worker retention must be positive")

        protected = protected_worker_ids or set()
        current_time = now if now is not None else datetime.now(UTC)
        removed: list[str] = []

        with self._lock:
            for worker_id, record in list(self._workers.items()):
                if record.status != "offline" or worker_id in protected:
                    continue

                age_seconds = (
                    current_time - record.last_seen_at
                ).total_seconds()
                if age_seconds < retention_seconds:
                    continue

                del self._workers[worker_id]
                if self._store is not None:
                    self._store.delete_record("workers", worker_id)
                removed.append(worker_id)

        return removed

    def clear(self) -> None:
        """Clear all workers; intended for tests and local development."""
        with self._lock:
            self._workers.clear()
            if self._store is not None:
                self._store.clear_records("workers")

    def heartbeat(self, worker_id: str) -> WorkerRecord | None:
        """Record a heartbeat from a known worker."""
        with self._lock:
            existing = self._workers.get(worker_id)
            if existing is None:
                return None

            updated = existing.model_copy(
                update={"last_seen_at": datetime.now(UTC), "status": "online"}
            )
            self._workers[worker_id] = updated
            self._persist(updated)
            return updated

    def mark_stale_workers(
        self,
        stale_after_seconds: float = 30.0,
        now: datetime | None = None,
    ) -> None:
        """Mark workers offline when their last heartbeat is too old."""
        if stale_after_seconds <= 0:
            raise ValueError("Stale timeout must be positive")

        with self._lock:
            current_time = now if now is not None else datetime.now(UTC)
            for worker_id, record in list(self._workers.items()):
                age_seconds = (current_time - record.last_seen_at).total_seconds()
                if record.status == "online" and age_seconds > stale_after_seconds:
                    updated = record.model_copy(update={"status": "offline"})
                    self._workers[worker_id] = updated
                    self._persist(updated)


worker_registry = WorkerRegistry(database_path=get_database_path())
