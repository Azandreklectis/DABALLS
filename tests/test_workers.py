
import pytest
from fastapi.testclient import TestClient

from daballs.controller.main import app
from daballs.controller.services.worker_registry import worker_registry


@pytest.fixture(autouse=True)
def reset_worker_registry():
    worker_registry.clear()
    yield
    worker_registry.clear()


def test_register_and_list_worker() -> None:
    client = TestClient(app)

    payload = {
        "worker_id": "worker-a",
        "hostname": "computer-a",
        "os_name": "Ubuntu",
        "architecture": "x86_64",
        "cpu_logical_cores": 8,
        "memory_total_bytes": 16 * 1024**3,
        "memory_available_bytes": 8 * 1024**3,
    }

    registration = client.post("/api/v1/workers/register", json=payload)

    assert registration.status_code == 200
    assert registration.json()["worker_id"] == "worker-a"
    assert registration.json()["status"] == "online"

    listing = client.get("/api/v1/workers")

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["hostname"] == "computer-a"


def test_register_worker_rejects_invalid_memory() -> None:
    client = TestClient(app)

    payload = {
        "worker_id": "worker-invalid",
        "hostname": "computer-invalid",
        "os_name": "Ubuntu",
        "architecture": "x86_64",
        "cpu_logical_cores": 8,
        "memory_total_bytes": 4 * 1024**3,
        "memory_available_bytes": 8 * 1024**3,
    }

    response = client.post("/api/v1/workers/register", json=payload)

    assert response.status_code == 422
    assert client.get("/api/v1/workers").json() == []

def test_reregistering_worker_updates_existing_record() -> None:
    client = TestClient(app)

    first_payload = {
        "worker_id": "worker-a",
        "hostname": "computer-a",
        "os_name": "Ubuntu",
        "architecture": "x86_64",
        "cpu_logical_cores": 8,
        "memory_total_bytes": 16 * 1024**3,
        "memory_available_bytes": 8 * 1024**3,
    }

    first_response = client.post(
        "/api/v1/workers/register",
        json=first_payload,
    )
    assert first_response.status_code == 200
    first_record = first_response.json()

    updated_payload = {
        **first_payload,
        "hostname": "computer-a-updated",
        "cpu_logical_cores": 12,
        "memory_available_bytes": 10 * 1024**3,
    }

    second_response = client.post(
        "/api/v1/workers/register",
        json=updated_payload,
    )
    assert second_response.status_code == 200
    second_record = second_response.json()

    workers_response = client.get("/api/v1/workers")
    workers = workers_response.json()

    assert len(workers) == 1
    assert second_record["worker_id"] == "worker-a"
    assert second_record["hostname"] == "computer-a-updated"
    assert second_record["cpu_logical_cores"] == 12
    assert second_record["memory_available_bytes"] == 10 * 1024**3
    assert second_record["registered_at"] == first_record["registered_at"]
    assert second_record["last_seen_at"] >= first_record["last_seen_at"]

    def test_heartbeat_updates_last_seen_timestamp() -> None:
        client = TestClient(app)

        payload = {
            "worker_id": "worker-heartbeat",
            "hostname": "computer-heartbeat",
            "os_name": "Ubuntu",
            "architecture": "x86_64",
            "cpu_logical_cores": 8,
            "memory_total_bytes": 16 * 1024 ** 3,
            "memory_available_bytes": 8 * 1024 ** 3,
        }

        registration = client.post(
            "/api/v1/workers/register",
            json=payload,
        )
        original = registration.json()

        response = client.post(
            "/api/v1/workers/worker-heartbeat/heartbeat",
        )

        assert response.status_code == 200
        updated = response.json()
        assert updated["worker_id"] == "worker-heartbeat"
        assert updated["registered_at"] == original["registered_at"]
        assert updated["last_seen_at"] >= original["last_seen_at"]
        assert updated["status"] == "online"

    def test_heartbeat_rejects_unknown_worker() -> None:
        client = TestClient(app)

        response = client.post(
            "/api/v1/workers/unknown-worker/heartbeat",
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Worker is not registered"