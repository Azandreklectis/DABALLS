
from fastapi.testclient import TestClient

from daballs.controller.main import app
from daballs.controller.services.worker_registry import worker_registry

client = TestClient(app)


def test_resource_offer_survives_registration_and_listing() -> None:
    worker_registry.clear()

    payload = {
        "worker_id": "resource-flow-test",
        "hostname": "test-host",
        "os_name": "Linux",
        "architecture": "x86_64",
        "cpu_logical_cores": 8,
        "memory_total_bytes": 16 * 1024**3,
        "memory_available_bytes": 8 * 1024**3,
        "offered_cpu_cores": 2,
        "offered_memory_bytes": 1024**3,
    }

    try:
        registration_response = client.post(
            "/api/v1/workers/register",
            json=payload,
        )

        assert registration_response.status_code == 200

        registered = registration_response.json()
        assert registered["offered_cpu_cores"] == 2
        assert registered["offered_memory_bytes"] == 1024**3

        listing_response = client.get("/api/v1/workers")

        assert listing_response.status_code == 200

        workers = listing_response.json()
        worker = next(
            item
            for item in workers
            if item["worker_id"] == "resource-flow-test"
        )

        assert worker["offered_cpu_cores"] == 2
        assert worker["offered_memory_bytes"] == 1024**3
    finally:
        worker_registry.clear()