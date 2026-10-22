
import pytest
from pydantic import ValidationError

from daballs.controller.domain.job import JobResultSubmission, JobSubmission
from daballs.controller.services.job_registry import JobRegistry

ARTIFACT_ID = "a" * 64


def test_legacy_sum_job_remains_valid() -> None:
    job = JobSubmission(
        worker_id="worker-1",
        workload_type="sum_integers",
        input_data=[1, 2, 3],
    )
    assert job.input_data == [1, 2, 3]
    assert job.artifact_id is None


def test_python_package_job_requires_artifact_id() -> None:
    with pytest.raises(ValidationError):
        JobSubmission(worker_id="worker-1", workload_type="python_package")


def test_python_package_job_accepts_artifact_id() -> None:
    job = JobSubmission(
        worker_id="worker-1",
        workload_type="python_package",
        artifact_id=ARTIFACT_ID,
    )
    assert job.artifact_id == ARTIFACT_ID
    assert job.input_data is None


def test_python_package_rejects_invalid_artifact_id() -> None:
    with pytest.raises(ValidationError):
        JobSubmission(
            worker_id="worker-1",
            workload_type="python_package",
            artifact_id="../bad",
        )


def test_result_submission_accepts_structured_result() -> None:
    result = JobResultSubmission(
        worker_id="worker-1",
        result_data={"accuracy": 0.95, "classes": ["setosa", "versicolor"]},
    )
    assert result.result_data["accuracy"] == 0.95


def test_result_submission_requires_exactly_one_payload() -> None:
    with pytest.raises(ValidationError):
        JobResultSubmission(worker_id="worker-1")

    with pytest.raises(ValidationError):
        JobResultSubmission(
            worker_id="worker-1",
            result=5,
            error="also failed",
        )


def test_registry_records_structured_result() -> None:
    registry = JobRegistry()
    submission = JobSubmission(
        worker_id="worker-1",
        workload_type="python_package",
        artifact_id=ARTIFACT_ID,
    )
    queued = registry.submit(submission)
    registry.claim_next("worker-1")

    result = {"accuracy": 0.95, "samples": 150}
    completed = registry.report_result(
        queued.job_id,
        "worker-1",
        result_data=result,
    )

    assert completed is not None
    assert completed.status == "completed"
    assert completed.result_data == result
    assert completed.result is None