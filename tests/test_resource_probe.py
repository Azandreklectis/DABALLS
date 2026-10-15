
from types import SimpleNamespace

import pytest

from daballs.controller.domain.worker import WorkerRegistration
from daballs.worker.resource_probe import probe_resources


def test_probe_resources_returns_registration_with_detected_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "daballs.worker.resource_probe.socket.gethostname",
        lambda: "test-host",
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.platform.system",
        lambda: "Linux",
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.platform.machine",
        lambda: "x86_64",
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.psutil.cpu_count",
        lambda logical: 8,
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.psutil.virtual_memory",
        lambda: SimpleNamespace(
            total=16 * 1024**3,
            available=8 * 1024**3,
        ),
    )

    registration = probe_resources("worker-test")

    assert isinstance(registration, WorkerRegistration)
    assert registration.worker_id == "worker-test"
    assert registration.hostname == "test-host"
    assert registration.os_name == "Linux"
    assert registration.architecture == "x86_64"
    assert registration.cpu_logical_cores == 8
    assert registration.memory_total_bytes == 16 * 1024**3
    assert registration.memory_available_bytes == 8 * 1024**3


def test_probe_resources_falls_back_when_cpu_count_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "daballs.worker.resource_probe.socket.gethostname",
        lambda: "test-host",
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.platform.system",
        lambda: "Linux",
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.platform.machine",
        lambda: "x86_64",
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.psutil.cpu_count",
        lambda logical: None,
    )
    monkeypatch.setattr(
        "daballs.worker.resource_probe.psutil.virtual_memory",
        lambda: SimpleNamespace(total=1024, available=512),
    )

    registration = probe_resources("worker-test")

    assert registration.cpu_logical_cores == 1
