
import pytest
from pydantic import ValidationError

from daballs.controller.domain.worker import WorkerRegistration


def make_registration(**overrides) -> WorkerRegistration:
    data = {
        "worker_id": "worker-offer-test",
        "hostname": "test-host",
        "os_name": "Linux",
        "architecture": "x86_64",
        "cpu_logical_cores": 8,
        "memory_total_bytes": 16 * 1024**3,
        "memory_available_bytes": 8 * 1024**3,
        "offered_cpu_cores": 4,
        "offered_memory_bytes": 2 * 1024**3,
    }
    data.update(overrides)
    return WorkerRegistration(**data)


def test_valid_resource_offer_is_accepted() -> None:
    registration = make_registration()

    assert registration.offered_cpu_cores == 4
    assert registration.offered_memory_bytes == 2 * 1024**3


def test_offer_cannot_exceed_logical_cpu_cores() -> None:
    with pytest.raises(ValidationError, match="Offered CPU cores"):
        make_registration(offered_cpu_cores=9)


def test_offer_cannot_exceed_total_memory() -> None:
    with pytest.raises(ValidationError, match="Offered memory"):
        make_registration(offered_memory_bytes=17 * 1024**3)


def test_omitted_offer_defaults_to_zero() -> None:
    registration = WorkerRegistration(
        worker_id="worker-no-offer",
        hostname="test-host",
        os_name="Linux",
        architecture="x86_64",
        cpu_logical_cores=8,
        memory_total_bytes=16 * 1024**3,
        memory_available_bytes=8 * 1024**3,
    )

    assert registration.offered_cpu_cores == 0
    assert registration.offered_memory_bytes == 0