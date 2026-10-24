import pytest
from pydantic import ValidationError

from daballs.controller.domain.job import JobSubmission
from daballs.controller.services.job_registry import JobRegistry

MEMORY_512_MIB = 512 * 1024**2
MEMORY_1_GIB = 1024**3


def make_submission(**overrides) -> JobSubmission:
    data = {
        "workload_type": "sum_integers",
        "input_data": [1, 2, 3],
    }
    data.update(overrides)
    return JobSubmission(**data)


def test_worker_id_is_optional_for_automatic_scheduling() -> None:
    submission = make_submission()

    assert submission.worker_id is None
    assert submission.required_cpu_cores == 1
    assert submission.required_memory_bytes == MEMORY_512_MIB


def test_resource_requirements_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        make_submission(required_cpu_cores=0)

    with pytest.raises(ValidationError):
        make_submission(required_memory_bytes=0)


def test_automatic_scheduler_selects_suitable_worker() -> None:
    registry = JobRegistry()
    capacities = {
        "small-worker": (1, MEMORY_512_MIB),
        "large-worker": (2, MEMORY_1_GIB),
    }

    job = registry.submit(make_submission(), worker_capacities=capacities)

    assert job.worker_id == "large-worker"
    assert job.status == "queued"


def test_queued_jobs_reserve_capacity() -> None:
    registry = JobRegistry()
    capacities = {"only-worker": (1, MEMORY_512_MIB)}

    first = registry.submit(make_submission(), worker_capacities=capacities)

    with pytest.raises(ValueError, match="No online worker"):
        registry.submit(make_submission(), worker_capacities=capacities)

    assert first.status == "queued"


def test_completed_job_releases_scheduler_capacity() -> None:
    registry = JobRegistry()
    capacities = {"only-worker": (1, MEMORY_512_MIB)}

    first = registry.submit(make_submission(), worker_capacities=capacities)
    assert registry.claim_next("only-worker") is not None

    completed = registry.report_result(
        first.job_id,
        "only-worker",
        result=6,
    )
    assert completed is not None
    assert completed.status == "completed"

    second = registry.submit(make_submission(), worker_capacities=capacities)
    assert second.worker_id == "only-worker"


def test_explicit_worker_assignment_is_preserved() -> None:
    registry = JobRegistry()
    capacities = {
        "worker-a": (2, MEMORY_1_GIB),
        "worker-b": (2, MEMORY_1_GIB),
    }

    job = registry.submit(
        make_submission(worker_id="worker-a"),
        worker_capacities=capacities,
    )

    assert job.worker_id == "worker-a"


def test_explicit_worker_rejects_insufficient_capacity() -> None:
    registry = JobRegistry()
    capacities = {"worker-a": (1, MEMORY_512_MIB)}

    registry.submit(
        make_submission(worker_id="worker-a"),
        worker_capacities=capacities,
    )

    with pytest.raises(ValueError, match="insufficient"):
        registry.submit(
            make_submission(worker_id="worker-a"),
            worker_capacities=capacities,
        )


def test_automatic_scheduling_fails_when_no_worker_is_online() -> None:
    registry = JobRegistry()

    with pytest.raises(ValueError, match="No online worker"):
        registry.submit(make_submission(), worker_capacities={})


def test_queued_job_is_reassigned_when_worker_goes_offline() -> None:
    registry = JobRegistry()
    original_capacities = {
        "worker-a": (1, MEMORY_512_MIB),
        "worker-b": (1, MEMORY_512_MIB),
    }
    job = registry.submit(
        make_submission(worker_id="worker-a"),
        worker_capacities=original_capacities,
    )

    registry.reconcile_workers({"worker-b": (1, MEMORY_512_MIB)})

    recovered = registry.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "queued"
    assert recovered.worker_id == "worker-b"


def test_running_job_fails_when_worker_goes_offline() -> None:
    registry = JobRegistry()
    original_capacities = {
        "worker-a": (1, MEMORY_512_MIB),
        "worker-b": (1, MEMORY_512_MIB),
    }
    job = registry.submit(
        make_submission(worker_id="worker-a"),
        worker_capacities=original_capacities,
    )
    assert registry.claim_next("worker-a") is not None

    registry.reconcile_workers({"worker-b": (1, MEMORY_512_MIB)})

    recovered = registry.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "failed"
    assert "went offline" in (recovered.error or "")

    # A terminal job no longer reserves capacity.
    replacement = registry.submit(
        make_submission(worker_id="worker-b"),
        worker_capacities={"worker-b": (1, MEMORY_512_MIB)},
    )
    assert replacement.status == "queued"


def test_queued_job_fails_if_no_worker_can_recover_it() -> None:
    registry = JobRegistry()
    job = registry.submit(
        make_submission(worker_id="worker-a"),
        worker_capacities={"worker-a": (1, MEMORY_512_MIB)},
    )

    registry.reconcile_workers({})

    recovered = registry.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "failed"
    assert "no online worker" in (recovered.error or "").lower()
