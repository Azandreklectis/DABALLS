"""Execute built-in and packaged Python workloads."""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from daballs.controller.domain.job import JobRecord
from daballs.worker.artifact_client import download_artifact, extract_artifact
from daballs.workloads.manifest import WorkloadManifest
from daballs.workloads.package_validator import WorkloadPackageError

logger = logging.getLogger(__name__)

MAX_LOG_CHARS = 1000
DEPENDENCY_INSTALL_TIMEOUT_SECONDS = 600


def _tail(text: str, limit: int = MAX_LOG_CHARS) -> str:
    """Keep error reports bounded."""
    return text[-limit:]


def execute_python_package(job: JobRecord, controller_url: str) -> dict[str, Any]:
    """Download, verify, and execute a packaged Python workload.

    Only execute packages from trusted sources. A virtual environment isolates
    Python dependencies but does not sandbox workload code from the host.
    """
    if not job.artifact_id:
        raise ValueError("Python package job is missing its artifact ID")

    archive_bytes = download_artifact(job.artifact_id, controller_url)

    runtime_base = Path(
        os.environ.get(
            "DABALLS_JOB_RUNTIME_DIR",
            str(Path.home() / ".daballs" / "jobs"),
        )
    ).expanduser()
    runtime_base.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f"{job.job_id}-",
        dir=runtime_base,
    ) as temporary_directory:
        root = Path(temporary_directory)
        package_dir = root / "package"
        extract_artifact(archive_bytes, package_dir)

        manifest_path = package_dir / "manifest.json"
        manifest = WorkloadManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )

        entrypoint = (package_dir / manifest.entrypoint).resolve()
        input_path = (package_dir / manifest.input_file).resolve()
        requirements_path = (package_dir / manifest.requirements_file).resolve()
        output_path = (package_dir / manifest.output_file).resolve()

        for path in (entrypoint, input_path, requirements_path, output_path):
            if not path.is_relative_to(package_dir.resolve()):
                raise WorkloadPackageError("Manifest path escapes the package directory")

        if not entrypoint.is_file() or not input_path.is_file():
            raise WorkloadPackageError("Workload entry point or input file is missing")

        environment_dir = root / "venv"
        create_environment = subprocess.run(
            [sys.executable, "-m", "venv", str(environment_dir)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if create_environment.returncode != 0:
            raise RuntimeError(
                "Could not create workload Python environment: "
                + _tail(create_environment.stderr or create_environment.stdout)
            )

        if requirements_path.read_text(encoding="utf-8").strip():
            python_executable = environment_dir / "bin" / "python"
            if os.name == "nt":
                python_executable = environment_dir / "Scripts" / "python.exe"

            install = subprocess.run(
                [
                    str(python_executable),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-input",
                    "-r",
                    str(requirements_path),
                ],
                cwd=package_dir,
                capture_output=True,
                text=True,
                timeout=DEPENDENCY_INSTALL_TIMEOUT_SECONDS,
                check=False,
            )
            if install.returncode != 0:
                raise RuntimeError(
                    "Workload dependency installation failed: "
                    + _tail(install.stderr or install.stdout)
                )

        python_executable = environment_dir / "bin" / "python"
        if os.name == "nt":
            python_executable = environment_dir / "Scripts" / "python.exe"

        try:
            execution = subprocess.run(
                [
                    str(python_executable),
                    str(entrypoint),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                cwd=package_dir,
                capture_output=True,
                text=True,
                timeout=manifest.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Workload exceeded its {manifest.timeout_seconds}-second timeout"
            ) from exc

        if execution.returncode != 0:
            details = _tail(execution.stderr or execution.stdout)
            raise RuntimeError(
                "Workload process failed"
                + (f": {details}" if details else "")
            )

        if not output_path.is_file():
            raise RuntimeError(
                f"Workload did not create its declared output file: "
                f"{manifest.output_file}"
            )

        try:
            result = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Workload output is not valid JSON") from exc

        if not isinstance(result, dict):
            raise TypeError("Workload output must be a JSON object")

        return result


def execute_job(
    job: JobRecord,
    controller_url: str | None = None,
) -> int | dict[str, Any]:
    """Execute a supported job and return its result."""
    if job.workload_type == "sum_integers":
        if job.input_data is None:
            raise ValueError("sum_integers job is missing input data")
        return sum(job.input_data)

    if job.workload_type == "python_package":
        if not controller_url:
            raise ValueError("Controller URL is required for Python package jobs")
        return execute_python_package(job, controller_url)

    raise ValueError(f"Unsupported workload type: {job.workload_type}")
