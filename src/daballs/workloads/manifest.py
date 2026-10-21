from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkloadManifest(BaseModel):
    """Metadata and execution settings for a packaged Python workload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    format_version: Literal[1]
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    entrypoint: str = Field(min_length=1, max_length=200)
    input_file: str = Field(min_length=1, max_length=200)
    requirements_file: str = Field(min_length=1, max_length=200)
    output_file: str = Field(min_length=1, max_length=200)
    timeout_seconds: int = Field(default=120, ge=1, le=3600)

    @field_validator(
        "entrypoint",
        "input_file",
        "requirements_file",
        "output_file",
    )
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        """Accept safe, relative POSIX paths only."""
        if (
            value.startswith("/")
            or "\\" in value
            or ":" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))
        ):
            raise ValueError("Paths must be safe relative POSIX paths")

        return value