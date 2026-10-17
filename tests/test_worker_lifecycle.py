from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from daballs.controller.domain.worker import WorkerRegistration
from daballs.controller.main import app
from daballs.controller.services.worker_registry import WorkerRegistry, worker_registry


def make_registration(worker_id: str) -> WorkerRegistration:
    return WorkerRegistration(
        worker_id=worker_id,
        hostname="test-host",
        os_name="Linux",
        architecture="x86_64",
        cpu_logical_cores=8,
        memory_total_bytes=16 * 1024**3,
        memory_available_bytes=8 * 1024**3,
    )


def test_stale_worker_is_marked_offline() -> None:
    registry = WorkerRegistry()
    registry.register(make_registration("worker-stale"))

    now = datetime.now(UTC) + timedelta(seconds=31)
    registry.mark_stale_workers(now=now)

    workers = registry.list_workers()

    assert len(workers) == 1
    assert workers[0].status == "offline"


def test_recent_worker_remains_online() -> None:
    registry = WorkerRegistry()
    registry.register(make_registration("worker-recent"))

    now = datetime.now(UTC) + timedelta(seconds=10)
    registry.mark_stale_workers(now=now)

    workers = registry.list_workers()

    assert workers[0].status == "online"


def test_stale_timeout_must_be_positive() -> None:
    registry = WorkerRegistry()

    with pytest.raises(ValueError, match="Stale timeout must be positive"):
        registry.mark_stale_workers(stale_after_seconds=0)


def test_offline_worker_recovers_after_heartbeat() -> None:
    client = TestClient(app)

    payload = {
        "worker_id": "worker-recovery",
        "hostname": "recovery-host",
        "os_name": "Linux",
        "architecture": "x86_64",
        "cpu_logical_cores": 8,
        "memory_total_bytes": 16 * 1024**3,
        "memory_available_bytes": 8 * 1024**3,
    }

    registration = client.post(
        "/api/v1/workers/register",
        json=payload,
    )
    assert registration.status_code == 200

    # Simulate a worker whose last heartbeat is over 30 seconds old.
    from datetime import UTC, datetime, timedelta

    future = datetime.now(UTC) + timedelta(seconds=31)
    worker_registry.mark_stale_workers(now=future)

    before_recovery = client.get("/api/v1/workers").json()
    worker = next(
        item for item in before_recovery
        if item["worker_id"] == "worker-recovery"
    )
    assert worker["status"] == "offline"

    response = client.post(
        "/api/v1/workers/worker-recovery/heartbeat",
    )

    assert response.status_code == 200
    recovered = response.json()
    assert recovered["status"] == "online"
    assert recovered["worker_id"] == "worker-recovery"
    assert recovered["last_seen_at"] > registration.json()["last_seen_at"]