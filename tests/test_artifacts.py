import hashlib
import io
import json
import zipfile

from fastapi.testclient import TestClient

from daballs.controller.main import app
from daballs.workloads.artifact_store import ArtifactStore


def make_archive() -> bytes:
    files = {
        "manifest.json": json.dumps({
            "format_version": 1,
            "name": "artifact-test",
            "entrypoint": "main.py",
            "input_file": "input.json",
            "requirements_file": "requirements.txt",
            "output_file": "result.json",
            "timeout_seconds": 60,
        }),
        "main.py": "print('hello')\n",
        "input.json": json.dumps({"value": 42}),
        "requirements.txt": "",
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)

    return buffer.getvalue()


def test_artifact_store_saves_and_retrieves(tmp_path) -> None:
    store = ArtifactStore(tmp_path)
    data = make_archive()

    metadata = store.save(data)

    assert metadata.artifact_id == hashlib.sha256(data).hexdigest()
    assert metadata.sha256 == metadata.artifact_id
    assert metadata.size_bytes == len(data)
    assert store.get_path(metadata.artifact_id).read_bytes() == data


def test_artifact_store_rejects_invalid_archive(tmp_path) -> None:
    from daballs.workloads.package_validator import WorkloadPackageError

    store = ArtifactStore(tmp_path)

    try:
        store.save(b"not a ZIP file")
    except WorkloadPackageError:
        pass
    else:
        raise AssertionError("Invalid archive should be rejected")


def test_artifact_store_returns_none_for_missing_artifact(tmp_path) -> None:
    store = ArtifactStore(tmp_path)

    assert store.get_metadata("a" * 64) is None


def test_artifact_store_rejects_invalid_id(tmp_path) -> None:
    store = ArtifactStore(tmp_path)

    try:
        store.get_path("../outside")
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid artifact ID should be rejected")


def test_artifact_upload_and_download(tmp_path, monkeypatch) -> None:
    import daballs.controller.api.v1.artifacts as artifacts_api

    store = ArtifactStore(tmp_path)
    monkeypatch.setattr(artifacts_api, "artifact_store", store)
    client = TestClient(app)
    data = make_archive()

    upload = client.post(
        "/api/v1/artifacts",
        content=data,
        headers={"Content-Type": "application/zip"},
    )

    assert upload.status_code == 201
    metadata = upload.json()
    artifact_id = metadata["artifact_id"]
    assert metadata["sha256"] == hashlib.sha256(data).hexdigest()

    metadata_response = client.get(
        f"/api/v1/artifacts/{artifact_id}/metadata"
    )
    assert metadata_response.status_code == 200
    assert metadata_response.json()["artifact_id"] == artifact_id

    download = client.get(f"/api/v1/artifacts/{artifact_id}")
    assert download.status_code == 200
    assert download.content == data


def test_artifact_upload_rejects_invalid_zip(tmp_path, monkeypatch) -> None:
    import daballs.controller.api.v1.artifacts as artifacts_api

    monkeypatch.setattr(artifacts_api, "artifact_store", ArtifactStore(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/v1/artifacts",
        content=b"invalid",
        headers={"Content-Type": "application/zip"},
    )

    assert response.status_code == 422


def test_artifact_download_returns_404_for_missing_id(tmp_path, monkeypatch) -> None:
    import daballs.controller.api.v1.artifacts as artifacts_api

    monkeypatch.setattr(artifacts_api, "artifact_store", ArtifactStore(tmp_path))
    client = TestClient(app)

    response = client.get(f"/api/v1/artifacts/{'a' * 64}")

    assert response.status_code == 404