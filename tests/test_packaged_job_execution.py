import hashlib
import io
import json
import zipfile

import pytest

from daballs.controller.domain.job import JobRecord
from daballs.worker.job_executor import execute_job


def make_package(
    script: str,
    *,
    requirements: str = "",
    timeout_seconds: int = 10,
) -> bytes:
    files = {
        "manifest.json": json.dumps(
            {
                "format_version": 1,
                "name": "test-job",
                "entrypoint": "main.py",
                "input_file": "input.json",
                "requirements_file": "requirements.txt",
                "output_file": "result.json",
                "timeout_seconds": timeout_seconds,
            }
        ),
        "main.py": script,
        "input.json": '{"value": 42}',
        "requirements.txt": requirements,
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def make_job(package: bytes) -> JobRecord:
    return JobRecord(
        worker_id="worker-test",
        workload_type="python_package",
        artifact_id=hashlib.sha256(package).hexdigest(),
    )


def patch_download(monkeypatch, package: bytes) -> None:
    monkeypatch.setattr(
        "daballs.worker.job_executor.download_artifact",
        lambda artifact_id, controller_url: package,
    )


def test_execute_python_package_returns_json_object(monkeypatch) -> None:
    package = make_package(
        """
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

data = json.loads(Path(args.input).read_text())
Path(args.output).write_text(json.dumps({"answer": data["value"] + 1}))
"""
    )
    patch_download(monkeypatch, package)

    result = execute_job(make_job(package), "http://controller.test:8000")

    assert result == {"answer": 43}


def test_execute_python_package_reports_nonzero_exit(monkeypatch) -> None:
    package = make_package('raise RuntimeError("intentional test failure")\n')
    patch_download(monkeypatch, package)

    with pytest.raises(RuntimeError, match="Workload process failed"):
        execute_job(make_job(package), "http://controller.test:8000")


def test_execute_python_package_requires_output_file(monkeypatch) -> None:
    package = make_package('print("no output file created")\n')
    patch_download(monkeypatch, package)

    with pytest.raises(RuntimeError, match="did not create"):
        execute_job(make_job(package), "http://controller.test:8000")


def test_execute_python_package_rejects_non_object_json(monkeypatch) -> None:
    package = make_package(
        """
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
Path(args.output).write_text("[1, 2, 3]")
"""
    )
    patch_download(monkeypatch, package)

    with pytest.raises(TypeError, match="JSON object"):
        execute_job(make_job(package), "http://controller.test:8000")


def test_execute_python_package_times_out(monkeypatch) -> None:
    package = make_package("import time\ntime.sleep(5)\n", timeout_seconds=1)
    patch_download(monkeypatch, package)

    with pytest.raises(TimeoutError, match="timeout"):
        execute_job(make_job(package), "http://controller.test:8000")
