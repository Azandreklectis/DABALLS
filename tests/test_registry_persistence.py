"""Tests for SQLite persistence across controller registry restarts."""

from datetime import UTC, datetime, timedelta

from daballs.controller.domain.job import JobSubmission
from daballs.controller.domain.worker import WorkerRegistration
from daballs.controller.services.job_registry import JobRegistry
from daballs.controller.services.worker_registry import WorkerRegistry


def make_registration(worker_id: str = "worker-persist") -> WorkerRegistration:
    return WorkerRegistration(
        worker_id=worker_id,
        display_name="Persistence Test Worker",
        hostname="test-host",
        os_name="Linux",
        architecture="x86_64",
        cpu_logical_cores=4,
        memory_total_bytes=4 * 1024**3,
        memory_available_bytes=3 * 1024**3,
        offered_cpu_cores=2,
        offered_memory_bytes=2 * 1024**3,
    )


def make_submission() -> JobSubmission:
    return JobSubmission(
        worker_id="worker-persist",
        workload_type="sum_integers",
        input_data=[1, 2, 3],
    )


def test_queued_job_survives_registry_restart(tmp_path):
    database = tmp_path / "controller.sqlite3"
    first = JobRegistry(database_path=database)
    created = first.submit(make_submission())

    restarted = JobRegistry(database_path=database)

    restored = restarted.get(created.job_id)
    assert restored is not None
    assert restored.status == "queued"
    assert restored.worker_id == "worker-persist"
    assert restored.input_data == [1, 2, 3]


def test_running_job_is_failed_after_registry_restart(tmp_path):
    database = tmp_path / "controller.sqlite3"
    first = JobRegistry(database_path=database)
    created = first.submit(make_submission())

    claimed = first.claim_next("worker-persist")
    assert claimed is not None
    assert claimed.job_id == created.job_id
    assert claimed.status == "running"

    restarted = JobRegistry(database_path=database)

    restored = restarted.get(created.job_id)
    assert restored is not None
    assert restored.status == "failed"
    assert "Controller restarted" in (restored.error or "")


def test_completed_job_and_result_survive_registry_restart(tmp_path):
    database = tmp_path / "controller.sqlite3"
    first = JobRegistry(database_path=database)
    created = first.submit(make_submission())
    assert first.claim_next("worker-persist") is not None

    completed = first.report_result(
        created.job_id,
        "worker-persist",
        result=6,
    )
    assert completed is not None
    assert completed.status == "completed"

    restarted = JobRegistry(database_path=database)

    restored = restarted.get(created.job_id)
    assert restored is not None
    assert restored.status == "completed"
    assert restored.result == 6


def test_saved_worker_is_restored_as_offline(tmp_path):
    database = tmp_path / "controller.sqlite3"
    first = WorkerRegistry(database_path=database)
    first.register(make_registration())

    restarted = WorkerRegistry(database_path=database)

    workers = restarted.list_workers()
    assert len(workers) == 1
    assert workers[0].worker_id == "worker-persist"
    assert workers[0].status == "offline"


def test_worker_can_reconnect_after_restart(tmp_path):
    database = tmp_path / "controller.sqlite3"
    first = WorkerRegistry(database_path=database)
    first.register(make_registration())

    restarted = WorkerRegistry(database_path=database)
    reconnected = restarted.register(make_registration())

    assert reconnected.status == "online"
    assert reconnected.worker_id == "worker-persist"


def test_clear_removes_persisted_jobs_and_workers(tmp_path):
    database = tmp_path / "controller.sqlite3"
    jobs = JobRegistry(database_path=database)
    workers = WorkerRegistry(database_path=database)

    created = jobs.submit(make_submission())
    workers.register(make_registration())

    jobs.clear()
    workers.clear()

    assert JobRegistry(database_path=database).get(created.job_id) is None
    assert WorkerRegistry(database_path=database).list_workers() == []


def test_expired_offline_worker_is_removed_from_memory_and_sqlite(tmp_path):
    database = tmp_path / "controller.sqlite3"
    registry = WorkerRegistry(database_path=database)
    registry.register(make_registration("worker-expired"))

    now = datetime.now(UTC) + timedelta(seconds=61)
    registry.mark_stale_workers(now=now)

    removed = registry.remove_expired_offline_workers(
        retention_seconds=60,
        now=now,
    )

    assert removed == ["worker-expired"]
    assert registry.list_workers() == []
    assert WorkerRegistry(database_path=database).list_workers() == []


def test_expired_worker_is_retained_while_active_job_references_it():
    registry = WorkerRegistry()
    registry.register(make_registration("worker-protected"))

    now = datetime.now(UTC) + timedelta(seconds=61)
    registry.mark_stale_workers(now=now)

    removed = registry.remove_expired_offline_workers(
        retention_seconds=60,
        now=now,
        protected_worker_ids={"worker-protected"},
    )

    assert removed == []
    assert len(registry.list_workers()) == 1
