import hashlib
import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest

from daballs.worker.artifact_client import (
    download_artifact,
    extract_artifact,
)
from daballs.workloads.package_validator import WorkloadPackageError


def make_package() -> bytes:
    files = {
        "manifest.json": json.dumps(
            {
                "format_version": 1,
                "name": "test-job",
                "entrypoint": "main.py",
                "input_file": "input.json",
                "requirements_file": "requirements.txt",
                "output_file": "result.json",
                "timeout_seconds": 10,
            }
        ),
        "main.py": 'print("hello")\n',
        "input.json": '{"value": 42}',
        "requirements.txt": "",
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_download_artifact_verifies_hash(monkeypatch) -> None:
    package = make_package()
    artifact_id = hashlib.sha256(package).hexdigest()

    def fake_get(url, timeout):
        assert url.endswith(f"/api/v1/artifacts/{artifact_id}")
        return httpx.Response(200, content=package, request=httpx.Request("GET", url))

    monkeypatch.setattr("daballs.worker.artifact_client.httpx.get", fake_get)

    assert download_artifact(artifact_id, "http://controller.test") == package


def test_download_artifact_rejects_hash_mismatch(monkeypatch) -> None:
    package = make_package()
    wrong_id = "a" * 64

    def fake_get(url, timeout):
        return httpx.Response(
            200,
            content=package,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr("daballs.worker.artifact_client.httpx.get", fake_get)

    with pytest.raises(WorkloadPackageError, match="hash"):
        download_artifact(wrong_id, "http://controller.test")


def test_download_artifact_rejects_invalid_id() -> None:
    with pytest.raises(ValueError, match="Invalid artifact ID"):
        download_artifact("../bad", "http://controller.test")


def test_extract_artifact_writes_validated_files(tmp_path: Path) -> None:
    package = make_package()

    extracted = extract_artifact(package, tmp_path / "job")

    assert (extracted / "main.py").read_text() == 'print("hello")\n'
    assert json.loads((extracted / "input.json").read_text()) == {"value": 42}
    assert (extracted / "requirements.txt").read_text() == ""


def test_extract_artifact_rejects_existing_target(tmp_path: Path) -> None:
    package = make_package()
    destination = tmp_path / "job"
    destination.mkdir()
    (destination / "main.py").write_text("keep me")

    with pytest.raises(WorkloadPackageError, match="already exists"):
        extract_artifact(package, destination)

    assert (destination / "main.py").read_text() == "keep me"
