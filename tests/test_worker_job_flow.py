
from daballs.controller.domain.job import JobRecord
from daballs.worker.agent import process_one_job


def make_job() -> JobRecord:
    return JobRecord(
        job_id="job-flow-test",
        worker_id="worker-test",
        workload_type="sum_integers",
        input_data=[10, 20, 30],
        status="running",
    )


def test_process_one_job_reports_success(monkeypatch) -> None:
    job = make_job()
    reported: dict[str, object] = {}

    def fake_claim(
        worker_id: str,
        controller_url: str,
    ) -> JobRecord:
        assert worker_id == "worker-test"
        return job

    def fake_report(
        job_id: str,
        controller_url: str,
        *,
        worker_id: str,
        result: int | None = None,
        error: str | None = None,
    ) -> JobRecord:
        reported["job_id"] = job_id
        reported["worker_id"] = worker_id
        reported["result"] = result
        reported["error"] = error
        return job.model_copy(
            update={"status": "completed", "result": result}
        )

    monkeypatch.setattr(
        "daballs.worker.agent.claim_next_job",
        fake_claim,
    )
    monkeypatch.setattr(
        "daballs.worker.agent.report_job_result",
        fake_report,
    )

    process_one_job("worker-test", "http://controller.test:8000")

    assert reported["job_id"] == "job-flow-test"
    assert reported["worker_id"] == "worker-test"
    assert reported["result"] == 60
    assert reported["error"] is None


def test_process_one_job_reports_execution_failure(monkeypatch) -> None:
    job = make_job()
    reported: dict[str, object] = {}

    def fake_claim(
        worker_id: str,
        controller_url: str,
    ) -> JobRecord:
        return job

    def fake_execute(received_job: JobRecord,
                        controller_url: str,) -> int:
        raise RuntimeError("Simulated execution failure")

    def fake_report(
        job_id: str,
        controller_url: str,
        *,
        worker_id: str,
        result: int | None = None,
        error: str | None = None,
    ) -> JobRecord:
        reported["job_id"] = job_id
        reported["worker_id"] = worker_id
        reported["result"] = result
        reported["error"] = error
        return job.model_copy(
            update={
                "status": "failed",
                "result": None,
                "error": error,
            }
        )

    monkeypatch.setattr(
        "daballs.worker.agent.claim_next_job",
        fake_claim,
    )
    monkeypatch.setattr(
        "daballs.worker.agent.execute_job",
        fake_execute,
    )
    monkeypatch.setattr(
        "daballs.worker.agent.report_job_result",
        fake_report,
    )

    process_one_job("worker-test", "http://controller.test:8000")

    assert reported["job_id"] == "job-flow-test"
    assert reported["worker_id"] == "worker-test"
    assert reported["result"] is None
    assert reported["error"] == "Simulated execution failure"