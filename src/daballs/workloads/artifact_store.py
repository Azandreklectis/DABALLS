import hashlib
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel

from daballs.workloads.manifest import WorkloadManifest
from daballs.workloads.package_validator import (
    MAX_ARCHIVE_BYTES,
    WorkloadPackageError,
    validate_workload_package,
)


def get_artifact_directory() -> Path:
    """Return persistent artifact storage outside the source tree."""
    configured = os.environ.get("DABALLS_ARTIFACT_DIR")
    if configured:
        return Path(configured).expanduser().resolve()

    return Path.home() / ".daballs" / "artifacts"


class ArtifactMetadata(BaseModel):
    artifact_id: str
    sha256: str
    size_bytes: int
    manifest: WorkloadManifest


class ArtifactStore:
    """Store validated workload archives by their SHA-256 digest."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or get_artifact_directory()

    def _artifact_path(self, artifact_id: str) -> Path:
        if (
            len(artifact_id) != 64
            or any(char not in "0123456789abcdef" for char in artifact_id)
        ):
            raise ValueError("Invalid artifact ID")

        return self.directory / f"{artifact_id}.zip"

    def save(self, archive_bytes: bytes) -> ArtifactMetadata:
        if not archive_bytes:
            raise WorkloadPackageError("Archive is empty")

        if len(archive_bytes) > MAX_ARCHIVE_BYTES:
            raise WorkloadPackageError("Archive exceeds the 50 MiB limit")

        validated = validate_workload_package(archive_bytes)
        digest = hashlib.sha256(archive_bytes).hexdigest()
        destination = self._artifact_path(digest)

        self.directory.mkdir(parents=True, exist_ok=True)

        if not destination.exists():
            temporary_path: Path | None = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=self.directory,
                    prefix=".upload-",
                    suffix=".tmp",
                    delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    temporary_file.write(archive_bytes)
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())

                os.replace(temporary_path, destination)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

        return ArtifactMetadata(
            artifact_id=digest,
            sha256=digest,
            size_bytes=len(archive_bytes),
            manifest=validated.manifest,
        )

    def get_metadata(self, artifact_id: str) -> ArtifactMetadata | None:
        path = self._artifact_path(artifact_id)

        if not path.is_file():
            return None

        archive_bytes = path.read_bytes()
        actual_digest = hashlib.sha256(archive_bytes).hexdigest()

        if actual_digest != artifact_id:
            raise WorkloadPackageError("Stored artifact hash does not match its ID")

        validated = validate_workload_package(archive_bytes)

        return ArtifactMetadata(
            artifact_id=artifact_id,
            sha256=actual_digest,
            size_bytes=len(archive_bytes),
            manifest=validated.manifest,
        )

    def get_path(self, artifact_id: str) -> Path | None:
        metadata = self.get_metadata(artifact_id)
        if metadata is None:
            return None

        return self._artifact_path(artifact_id)


artifact_store = ArtifactStore()