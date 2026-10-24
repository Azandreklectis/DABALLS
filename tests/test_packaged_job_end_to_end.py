"""End-to-end acceptance test for packaged Python workloads."""

import io
import json
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient

from daballs.controller.domain.job import JobRecord, JobResultSubmission
from daballs.controller.main import app
from daballs.controller.services.job_registry import job_registry
from daballs.controller.services.worker_registry import worker_registry
from daballs.worker.agent import process_one_job
from daballs.workloads.artifact_store import ArtifactStore


@pytest.fixture
def client_and_clean_state():
    worker_registry.clear()
    job_registry.clear()

    with TestClient(app) as client:
        yield client

    worker_registry.clear()
    job_registry.clear()


def make_package() -> bytes:
    """Build a small package that needs no third-party dependencies."""
    files = {
        "manifest.json": json.dumps(
            {
                "format_version": 1,
                "name": "end-to-end-test",
                "entrypoint": "main.py",
                "input_file": "input.json",
                "requirements_file": "requirements.txt",
                "output_file": "result.json",
                "timeout_seconds": 30,
            }
        ),
        "input.json": json.dumps({"value": 41}),
        "requirements.txt": "",
        "main.py": (
            "import argparse\n"
            "import json\n"
            "\n"
            "parser = argparse.ArgumentParser()\n"
            'parser.add_argument("--input", required=True)\n'
            'parser.add_argument("--output", required=True)\n'
            "args = parser.parse_args()\n"
            "\n"
            'with open(args.input, encoding="utf-8") as source:\n'
            "    data = json.load(source)\n"
            "\n"
            "result = {\n"
            '    "answer": data["value"] + 1,\n'
            '    "execution": "successful",\n'
            "}\n"
            'with open(args.output, "w", encoding="utf-8") as target:\n'
            "    json.dump(result, target)\n"
        ),
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)

    return buffer.getvalue()


def test_packaged_job_runs_through_controller_and_worker(
    tmp_path,
    monkeypatch,
    client_and_clean_state,
) -> None:
    client = client_and_clean_state
    controller_url = "http://controller.test"

    # Isolate artifact storage and job runtime from the user's real directories.
    import daballs.controller.api.v1.artifacts as artifacts_api

    monkeypatch.setattr(
        artifacts_api,
        "artifact_store",
        ArtifactStore(tmp_path / "artifacts"),
    )
    monkeypatch.setenv(
        "DABALLS_JOB_RUNTIME_DIR",
        str(tmp_path / "job-runtime"),
    )

    # 1. Upload a valid Python package.
    package_bytes = make_package()
    upload = client.post(
        "/api/v1/artifacts",
        content=package_bytes,
        headers={"Content-Type": "application/zip"},
    )

    assert upload.status_code == 201, upload.text
    artifact_id = upload.json()["artifact_id"]

    # 2. Register an online worker.
    registration = client.post(
        "/api/v1/workers/register",
        json={
            "worker_id": "e2e-worker",
            "display_name": "End-to-end test worker",
            "hostname": "test-host",
            "os_name": "Linux",
            "architecture": "x86_64",
            "cpu_logical_cores": 4,
            "memory_total_bytes": 4 * 1024**3,
            "memory_available_bytes": 2 * 1024**3,
            "offered_cpu_cores": 1,
            "offered_memory_bytes": 512 * 1024**2,
        },
    )

    assert registration.status_code == 200, registration.text
    assert registration.json()["status"] == "online"

    # 3. Submit a job that references the uploaded artifact.
    submission = client.post(
        "/api/v1/jobs",
        json={
            "worker_id": "e2e-worker",
            "workload_type": "python_package",
            "artifact_id": artifact_id,
        },
    )

    assert submission.status_code == 201, submission.text
    job_id = submission.json()["job_id"]
    assert submission.json()["status"] == "queued"

    # 4. Route the worker's artifact download to the test controller.
    # The package bytes still come from the artifact API and are hash-verified
    # by the real worker artifact client.
    def fake_download_get(
        url: str,
        timeout: float,
        headers: dict | None = None,
    ) -> httpx.Response:
        assert timeout == 30
        assert url.endswith(f"/api/v1/artifacts/{artifact_id}")
        return client.get(f"/api/v1/artifacts/{artifact_id}")

    monkeypatch.setattr(
        "daballs.worker.artifact_client.httpx.get",
        fake_download_get,
    )

    # Route the worker's claim and result-report calls through the real API.
    def api_claim(
        worker_id: str,
        received_controller_url: str,
    ) -> JobRecord | None:
        assert received_controller_url == controller_url
        response = client.post(
            "/api/v1/jobs/next",
            params={"worker_id": worker_id},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        return JobRecord.model_validate(data) if data is not None else None

    def api_report(
        received_job_id: str,
        received_controller_url: str,
        *,
        worker_id: str,
        result: int | None = None,
        result_data: dict | None = None,
        error: str | None = None,
    ) -> JobRecord:
        assert received_controller_url == controller_url
        payload = JobResultSubmission(
            worker_id=worker_id,
            result=result,
            result_data=result_data,
            error=error,
        )
        response = client.post(
            f"/api/v1/jobs/{received_job_id}/result",
            json=payload.model_dump(mode="json"),
        )
        assert response.status_code == 200, response.text
        return JobRecord.model_validate(response.json())

    monkeypatch.setattr("daballs.worker.agent.claim_next_job", api_claim)
    monkeypatch.setattr("daballs.worker.agent.report_job_result", api_report)

    # 5. Run the actual worker flow and actual Python package executor.
    process_one_job("e2e-worker", controller_url)

    # 6. Verify the controller persisted the structured result.
    completed_response = client.get(f"/api/v1/jobs/{job_id}")
    assert completed_response.status_code == 200

    completed = completed_response.json()
    assert completed["status"] == "completed"
    assert completed["result"] is None
    assert completed["error"] is None
    assert completed["result_data"] == {
        "answer": 42,
        "execution": "successful",
    }
