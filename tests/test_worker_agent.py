
from datetime import UTC, datetime

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

    def fake_probe(worker_id: str) -> WorkerRegistration:
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