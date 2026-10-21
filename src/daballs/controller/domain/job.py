
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

ArtifactId = str


class JobSubmission(BaseModel):
    """A request to run a supported workload on a chosen worker."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)
    workload_type: Literal["sum_integers", "python_package"]
    input_data: list[int] | None = Field(default=None, min_length=1, max_length=10_000)
    artifact_id: ArtifactId | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )

    @model_validator(mode="after")
    def validate_workload_fields(self) -> "JobSubmission":
        if self.workload_type == "sum_integers":
            if self.input_data is None:
                raise ValueError("sum_integers requires input_data")
            if self.artifact_id is not None:
                raise ValueError("sum_integers does not accept artifact_id")
        else:
            if self.artifact_id is None:
                raise ValueError("python_package requires artifact_id")
            if self.input_data is not None:
                raise ValueError("python_package uses the input bundled in its artifact")
        return self


class JobResultSubmission(BaseModel):
    """A worker's successful result or failure report."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)
    result: int | None = None
    result_data: dict[str, Any] | None = None
    error: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_result_or_error(self) -> "JobResultSubmission":
        supplied = sum(
            value is not None
            for value in (self.result, self.result_data, self.error)
        )
        if supplied != 1:
            raise ValueError("Provide exactly one of result, result_data, or error")
        return self


class JobRecord(BaseModel):
    """A job as tracked by the controller."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    worker_id: str
    workload_type: Literal["sum_integers", "python_package"]
    input_data: list[int] | None = None
    artifact_id: ArtifactId | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    result: int | None = None
    result_data: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_workload_fields(self) -> "JobRecord":
        if self.workload_type == "sum_integers":
            if self.input_data is None:
                raise ValueError("sum_integers requires input_data")
            if self.artifact_id is not None:
                raise ValueError("sum_integers does not accept artifact_id")
        else:
            if self.artifact_id is None:
                raise ValueError("python_package requires artifact_id")
            if self.input_data is not None:
                raise ValueError("python_package does not accept input_data")
        return self