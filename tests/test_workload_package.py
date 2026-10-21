import io
import json
import zipfile

import pytest

from daballs.workloads.package_validator import (
    WorkloadPackageError,
    validate_workload_package,
)

MANIFEST = {
    "format_version": 1,
    "name": "test-workload",
    "entrypoint": "main.py",
    "input_file": "input.json",
    "requirements_file": "requirements.txt",
    "output_file": "result.json",
    "timeout_seconds": 120,
}

FILES = {
    "manifest.json": json.dumps(MANIFEST),
    "main.py": "print('hello')\n",
    "input.json": json.dumps({"value": 1}),
    "requirements.txt": "scikit-learn>=1.4,<2.0\n",
}


def make_archive(files: dict[str, str] | None = None) -> bytes:
    buffer = io.BytesIO()
    contents = FILES if files is None else files

    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in contents.items():
            archive.writestr(name, content)

    return buffer.getvalue()


def test_valid_package_is_accepted() -> None:
    validated = validate_workload_package(make_archive())

    assert validated.manifest.name == "test-workload"
    assert validated.manifest.format_version == 1
    assert "main.py" in validated.member_names


def test_missing_required_file_is_rejected() -> None:
    files = dict(FILES)
    del files["main.py"]

    with pytest.raises(WorkloadPackageError, match="Missing required files"):
        validate_workload_package(make_archive(files))


def test_invalid_manifest_version_is_rejected() -> None:
    files = dict(FILES)
    manifest = dict(MANIFEST)
    manifest["format_version"] = 99
    files["manifest.json"] = json.dumps(manifest)

    with pytest.raises(WorkloadPackageError, match="Invalid manifest"):
        validate_workload_package(make_archive(files))


def test_path_traversal_is_rejected() -> None:
    files = dict(FILES)
    files["../outside.txt"] = "not allowed"

    with pytest.raises(WorkloadPackageError, match="Unsafe archive path"):
        validate_workload_package(make_archive(files))


def test_manifest_cannot_reference_missing_entrypoint() -> None:
    files = dict(FILES)
    manifest = dict(MANIFEST)
    manifest["entrypoint"] = "missing.py"
    files["manifest.json"] = json.dumps(manifest)

    with pytest.raises(WorkloadPackageError, match="references missing files"):
        validate_workload_package(make_archive(files))


def test_output_file_must_not_be_in_uploaded_package() -> None:
    files = dict(FILES)
    files["result.json"] = json.dumps({"unexpected": True})

    with pytest.raises(WorkloadPackageError, match="output file"):
        validate_workload_package(make_archive(files))


def test_input_must_be_a_json_object() -> None:
    files = dict(FILES)
    files["input.json"] = json.dumps([1, 2, 3])

    with pytest.raises(WorkloadPackageError, match="JSON object"):
        validate_workload_package(make_archive(files))


def test_pip_install_directives_are_rejected() -> None:
    files = dict(FILES)
    files["requirements.txt"] = "--index-url https://example.invalid/simple\n"

    with pytest.raises(WorkloadPackageError, match="Unsupported requirement syntax"):
        validate_workload_package(make_archive(files))


def test_corrupt_zip_is_rejected() -> None:
    with pytest.raises(WorkloadPackageError, match="valid ZIP"):
        validate_workload_package(b"this is not a ZIP archive")


def test_unsafe_manifest_path_is_rejected() -> None:
    files = dict(FILES)
    manifest = dict(MANIFEST)
    manifest["entrypoint"] = "../main.py"
    files["manifest.json"] = json.dumps(manifest)

    with pytest.raises(WorkloadPackageError, match="Invalid manifest"):
        validate_workload_package(make_archive(files))