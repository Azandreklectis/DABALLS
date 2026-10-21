import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, BinaryIO

from pydantic import ValidationError

from daballs.workloads.manifest import WorkloadManifest

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_MEMBER_BYTES = 20 * 1024 * 1024
MAX_MEMBERS = 100

REQUIRED_FILES = {"manifest.json", "main.py", "input.json", "requirements.txt"}

# Deliberately accept ordinary package requirements, not pip options,
# direct URLs, local paths, editable installs, or other install directives.
REQUIREMENT_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*"
    r"(?:\[[A-Za-z0-9._,-]+\])?"
    r"(?:\s*(?:===|==|!=|~=|>=|<=|>|<)\s*[A-Za-z0-9.*_+-]+"
    r"(?:\s*,\s*(?:===|==|!=|~=|>=|<=|>|<)\s*[A-Za-z0-9.*_+-]+)*)?$"
)


class WorkloadPackageError(ValueError):
    """Raised when a workload archive violates the package contract."""


@dataclass(frozen=True)
class ValidatedWorkloadPackage:
    """Validated package metadata and archive file names."""

    manifest: WorkloadManifest
    member_names: tuple[str, ...]


def _read_archive(source: bytes | bytearray | BinaryIO) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
    else:
        data = source.read(MAX_ARCHIVE_BYTES + 1)

    if len(data) > MAX_ARCHIVE_BYTES:
        raise WorkloadPackageError("Archive exceeds the 50 MiB limit")

    if not data:
        raise WorkloadPackageError("Archive is empty")

    return data


def _validate_member_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise WorkloadPackageError(f"Unsafe archive path: {name!r}")

    # ZIP paths use POSIX separators. Directories may end with one slash.
    normalized = name.removesuffix("/")
    path = PurePosixPath(normalized)

    if (
        not normalized
        or path.is_absolute()
        or ":" in normalized
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise WorkloadPackageError(f"Unsafe archive path: {name!r}")

    return normalized


def _validate_requirements(text: str) -> None:
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        requirement = raw_line.strip()

        if not requirement or requirement.startswith("#"):
            continue

        if not REQUIREMENT_PATTERN.fullmatch(requirement):
            raise WorkloadPackageError(
                f"Unsupported requirement syntax on line {line_number}: "
                f"{requirement!r}"
            )


def validate_workload_package(
    source: bytes | bytearray | BinaryIO,
) -> ValidatedWorkloadPackage:
    """Validate an uploaded workload ZIP without extracting or executing it."""
    archive_bytes = _read_archive(source)

    try:
        archive = zipfile.ZipFile(__import__("io").BytesIO(archive_bytes))
    except (zipfile.BadZipFile, OSError) as exc:
        raise WorkloadPackageError("File is not a valid ZIP archive") from exc

    with archive:
        entries = archive.infolist()

        if len(entries) > MAX_MEMBERS:
            raise WorkloadPackageError(
                f"Archive contains more than {MAX_MEMBERS} entries"
            )

        files: dict[str, zipfile.ZipInfo] = {}
        total_uncompressed = 0

        for entry in entries:
            name = _validate_member_name(entry.filename)

            # Reject duplicate file paths and file/directory collisions.
            if name in files:
                raise WorkloadPackageError(f"Duplicate archive path: {name!r}")

            unix_mode = entry.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                raise WorkloadPackageError(
                    f"Symbolic links are not permitted: {name!r}"
                )

            if entry.flag_bits & 0x1:
                raise WorkloadPackageError("Encrypted ZIP entries are not supported")

            if entry.is_dir():
                continue

            if entry.file_size > MAX_MEMBER_BYTES:
                raise WorkloadPackageError(
                    f"Archive member exceeds the 20 MiB limit: {name!r}"
                )

            total_uncompressed += entry.file_size
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise WorkloadPackageError(
                    "Archive exceeds the 100 MiB uncompressed-size limit"
                )

            files[name] = entry

        missing = REQUIRED_FILES - files.keys()
        if missing:
            raise WorkloadPackageError(
                f"Missing required files: {', '.join(sorted(missing))}"
            )

        try:
            manifest_data = json.loads(archive.read(files["manifest.json"]))
            manifest = WorkloadManifest.model_validate(manifest_data)
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as exc:
            raise WorkloadPackageError(f"Invalid manifest: {exc}") from exc

        declared_files = {
            manifest.entrypoint,
            manifest.input_file,
            manifest.requirements_file,
        }

        missing_declared = declared_files - files.keys()
        if missing_declared:
            raise WorkloadPackageError(
                "Manifest references missing files: "
                + ", ".join(sorted(missing_declared))
            )

        if manifest.output_file in files:
            raise WorkloadPackageError(
                "The output file must not already exist in the uploaded package"
            )

        try:
            input_data: Any = json.loads(archive.read(files[manifest.input_file]))
            if not isinstance(input_data, dict):
                raise WorkloadPackageError("input.json must contain a JSON object")

            requirements_text = archive.read(
                files[manifest.requirements_file]
            ).decode("utf-8")
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise WorkloadPackageError(
                f"Invalid input or requirements file: {exc}"
            ) from exc

        _validate_requirements(requirements_text)

        return ValidatedWorkloadPackage(
            manifest=manifest,
            member_names=tuple(sorted(files)),
        )