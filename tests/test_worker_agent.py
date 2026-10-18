
import sys
from datetime import UTC, datetime
from threading import Event

import pytest

from daballs.controller.domain.worker import WorkerRecord, WorkerRegistration
from daballs.worker.agent import run_agent


def test_run_agent_probes_and_registers_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    def fake_probe(
            worker_id: str,
            offered_cpu_cores: int = 0,
            offered_memory_bytes: int = 0,
            display_name: str | None = None,
    ) -> WorkerRegistration:
        assert worker_id == "worker-test"
        return registration

    def fake_register(
        received_registration: WorkerRegistration,
        controller_url: str,
    ) -> WorkerRecord:
        assert received_registration == registration
        assert controller_url == "http://controller.test:8000"
        return expected_record

    monkeypatch.setattr("daballs.worker.agent.probe_resources", fake_probe)
    monkeypatch.setattr(
        "daballs.worker.agent.register_with_controller",
        fake_register,
    )

    result = run_agent("worker-test", "http://controller.test:8000")

    assert result == expected_record


def test_run_forever_sends_heartbeat_and_stops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from daballs.controller.domain.worker import WorkerRecord
    from daballs.worker.agent import run_forever

    stop_event = Event()
    calls = {"registration": 0, "heartbeat": 0}

    def fake_run_agent(
            worker_id: str,
            controller_url: str,
            offered_cpu_cores: int = 0,
            offered_memory_bytes: int = 0,
            display_name: str | None = None,
    ) -> WorkerRecord:
        calls["registration"] += 1
        return WorkerRecord(
            worker_id=worker_id,
            hostname="test-host",
            os_name="Linux",
            architecture="x86_64",
            cpu_logical_cores=8,
            memory_total_bytes=16 * 1024**3,
            memory_available_bytes=8 * 1024**3,
            status="online",
            registered_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        )


    def fake_send_heartbeat(
        worker_id: str,
        controller_url: str,
    ) -> WorkerRecord:
        calls["heartbeat"] += 1
        stop_event.set()

        return WorkerRecord(
            worker_id=worker_id,
            hostname="test-host",
            os_name="Linux",
            architecture="x86_64",
            cpu_logical_cores=8,
            memory_total_bytes=16 * 1024**3,
            memory_available_bytes=8 * 1024**3,
            status="online",
            registered_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
        )

    monkeypatch.setattr("daballs.worker.agent.run_agent", fake_run_agent)
    monkeypatch.setattr(
        "daballs.worker.agent.send_heartbeat",
        fake_send_heartbeat,
    )

    run_forever(
        "worker-test",
        "http://controller.test:8000",
        heartbeat_interval=0.001,
        stop_event=stop_event,
    )

    assert calls["registration"] == 1
    assert calls["heartbeat"] == 1


def test_main_passes_resource_offers_to_run_forever(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    from daballs.worker.agent import main

    received: dict[str, object] = {}

    def fake_run_forever(**kwargs: object) -> None:
        received.update(kwargs)

    monkeypatch.setattr(
        "daballs.worker.agent.run_forever",
        fake_run_forever,
    )
    monkeypatch.setattr(
        "daballs.worker.agent.get_or_create_worker_id",
        lambda: "worker-test",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "daballs-worker",
            "--controller-url",
            "http://controller.test:8000",
            "--offer-cpu-cores",
            "2",
            "--offer-memory-mib",
            "1024",
        ],
    )

    main()

    assert received["worker_id"] == "worker-test"
    assert received["controller_url"] == "http://controller.test:8000"
    assert received["offered_cpu_cores"] == 2
    assert received["offered_memory_bytes"] == 1024 * 1024**2