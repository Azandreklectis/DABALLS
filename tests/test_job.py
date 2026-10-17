
from fastapi.testclient import TestClient

from daballs.controller.domain.worker import WorkerRegistration
from daballs.controller.main import app
from daballs.controller.services.job_registry import job_registry
from daballs.controller.services.worker_registry import worker_registry

client = TestClient(app)


def register_test_worker() -> None:
    worker_registry.register(
        WorkerRegistration(
            worker_id="job-test-worker",
            hostname="test-host",
            os_name="Linux",
            architecture="x86_64",
            cpu_logical_cores=8,
            memory_total_bytes=16 * 1024**3,
            memory_available_bytes=8 * 1024**3,
            offered_cpu_cores=2,
            offered_memory_bytes=1024**3,
        )
    )


def test_job_submission_claim_and_result() -> None:
    worker_registry.clear()
    job_registry.clear()
    register_test_worker()

    try:
        response = client.post(
            "/api/v1/jobs",
            json={
                "worker_id": "job-test-worker",
                "workload_type": "sum_integers",
                "input_data": [10, 20, 30],
            },
        )

        assert response.status_code == 201
        submitted = response.json()
        assert submitted["status"] == "queued"
        job_id = submitted["job_id"]

        claim_response = client.post(
            "/api/v1/jobs/next",
            params={"worker_id": "job-test-worker"},
        )

        assert claim_response.status_code == 200
        assert claim_response.json()["job_id"] == job_id
        assert claim_response.json()["status"] == "running"

        result_response = client.post(
            f"/api/v1/jobs/{job_id}/result",
            json={
                "worker_id": "job-test-worker",
                "result": 60,
            },
        )

        assert result_response.status_code == 200
        assert result_response.json()["status"] == "completed"
        assert result_response.json()["result"] == 60

        get_response = client.get(f"/api/v1/jobs/{job_id}")
        assert get_response.status_code == 200
        assert get_response.json()["result"] == 60
    finally:
        job_registry.clear()
        worker_registry.clear()


def test_job_submission_rejects_unknown_worker() -> None:
    worker_registry.clear()
    job_registry.clear()

    try:
        response = client.post(
            "/api/v1/jobs",
            json={
                "worker_id": "unknown-worker",
                "workload_type": "sum_integers",
                "input_data": [1, 2, 3],
            },
        )

        assert response.status_code == 404
    finally:
        job_registry.clear()
        worker_registry.clear()


def test_job_failure_can_be_reported() -> None:
    worker_registry.clear()
    job_registry.clear()
    register_test_worker()

    try:
        response = client.post(
            "/api/v1/jobs",
            json={
                "worker_id": "job-test-worker",
                "workload_type": "sum_integers",
                "input_data": [1, 2],
            },
        )
        assert response.status_code == 201
        job_id = response.json()["job_id"]

        claim_response = client.post(
            "/api/v1/jobs/next",
            params={"worker_id": "job-test-worker"},
        )
        assert claim_response.status_code == 200

        failure_response = client.post(
            f"/api/v1/jobs/{job_id}/result",
            json={
                "worker_id": "job-test-worker",
                "error": "Test execution failure",
            },
        )

        assert failure_response.status_code == 200
        assert failure_response.json()["status"] == "failed"
        assert failure_response.json()["error"] == "Test execution failure"
    finally:
        job_registry.clear()
        worker_registry.clear()