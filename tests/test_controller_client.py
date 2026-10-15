
from datetime import UTC, datetime

import httpx

from daballs.controller.domain.worker import WorkerRecord, WorkerRegistration
from daballs.worker.controller_client import register_with_controller


def test_register_with_controller(monkeypatch) -> None:
    registration = WorkerRegistration(
        worker_id="worker-test",
        hostname="test-host",
        os_name="Linux",
        architecture="x86_64",
        cpu_logical_cores=8,
        memory_total_bytes=16 * 1024**3,
        memory_available_bytes=8 * 1024**3,
    )

    expected_record = WorkerRecord(
        **registration.model_dump(),
        status="online",
        registered_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
    )

    def fake_post(url, **kwargs):
        assert url == "http://127.0.0.1:8000/api/v1/workers/register"
        assert kwargs["json"]["worker_id"] == "worker-test"
        assert kwargs["timeout"] == 5.0

        return httpx.Response(
            200,
            json=expected_record.model_dump(mode="json"),
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "daballs.worker.controller_client.httpx.post",
        fake_post,
    )

    result = register_with_controller(
        registration,
        "http://127.0.0.1:8000/",
    )

    assert result.worker_id == "worker-test"
    assert result.status == "online"
    assert isinstance(result, WorkerRecord)


def test_send_heartbeat(monkeypatch) -> None:
    from datetime import UTC, datetime

    from daballs.worker.controller_client import send_heartbeat

    registered_at = datetime.now(UTC)
    last_seen_at = datetime.now(UTC)

    expected_record = WorkerRecord(
        worker_id="worker-test",
        hostname="test-host",
        os_name="Linux",
        architecture="x86_64",
        cpu_logical_cores=8,
        memory_total_bytes=16 * 1024**3,
        memory_available_bytes=8 * 1024**3,
        status="online",
        registered_at=registered_at,
        last_seen_at=last_seen_at,
    )

    def fake_post(url, **kwargs):
        assert url == (
            "http://127.0.0.1:8000/api/v1/workers/"
            "worker-test/heartbeat"
        )
        assert kwargs["timeout"] == 5.0

        return httpx.Response(
            200,
            json=expected_record.model_dump(mode="json"),
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(
        "daballs.worker.controller_client.httpx.post",
        fake_post,
    )

    result = send_heartbeat(
        "worker-test",
        "http://127.0.0.1:8000/",
    )

    assert result.worker_id == "worker-test"
    assert result.status == "online"
    assert isinstance(result, WorkerRecord)