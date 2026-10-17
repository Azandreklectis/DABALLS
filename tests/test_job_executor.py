

from daballs.controller.domain.job import JobRecord
from daballs.worker.job_executor import execute_job


def make_job(input_data: list[int]) -> JobRecord:
    return JobRecord(
        worker_id="worker-test",
        workload_type="sum_integers",
        input_data=input_data,
    )


def test_execute_sum_integers() -> None:
    job = make_job([10, 20, 30])

    assert execute_job(job) == 60


def test_execute_sum_integers_with_negative_values() -> None:
    job = make_job([-5, 10, -2])

    assert execute_job(job) == 3


def test_execute_sum_integers_with_zero() -> None:
    job = make_job([0, 0, 0])

    assert execute_job(job) == 0