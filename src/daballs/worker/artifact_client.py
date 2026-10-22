"""Download and safely extract validated workload artifacts."""

import hashlib
import io
import zipfile
from pathlib import Path, PurePosixPath

import httpx

from daballs.workloads.package_validator import (
    MAX_ARCHIVE_BYTES,
    WorkloadPackageError,
    validate_workload_package,
)


def download_artifact(artifact_id: str, controller_url: str) -> bytes:
    """Download an artifact and verify its content-addressed SHA-256 ID."""
    if (
        len(artifact_id) != 64
        or any(char not in "0123456789abcdef" for char in artifact_id)
    ):
        raise ValueError("Invalid artifact ID")

    url = (
        f"{controller_url.rstrip('/')}"
        f"/api/v1/artifacts/{artifact_id}"
    )
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    archive_bytes = response.content

    if len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise WorkloadPackageError("Archive exceeds the 50 MiB limit")

    actual_digest = hashlib.sha256(archive_bytes).hexdigest()
    if actual_digest != artifact_id:
        raise WorkloadPackageError(
            "Downloaded artifact hash does not match its ID"
        )

    validate_workload_package(archive_bytes)
    return archive_bytes


def extract_artifact(archive_bytes: bytes, destination: Path) -> Path:
    """Validate and extract regular package files beneath a destination."""
    validated = validate_workload_package(archive_bytes)
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()

    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            entries = {
                info.filename: info
                for info in archive.infolist()
                if not info.is_dir()
            }

            for name in validated.member_names:
                info = entries[name]
                relative_path = PurePosixPath(name)
                target = root.joinpath(*relative_path.parts)

                # Defend against path traversal even after package validation.
                resolved_target = target.resolve()
                if not resolved_target.is_relative_to(root):
                    raise WorkloadPackageError(
                        f"Unsafe extraction path: {name!r}"
                    )

                target.parent.mkdir(parents=True, exist_ok=True)

                if target.exists():
                    raise WorkloadPackageError(
                        f"Extraction target already exists: {name!r}"
                    )

                with archive.open(info) as source, target.open("xb") as output:
                    while chunk := source.read(64 * 1024):
                        output.write(chunk)

    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        raise WorkloadPackageError(
            f"Could not extract workload package: {exc}"
        ) from exc

    return root
