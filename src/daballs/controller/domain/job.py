
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobSubmission(BaseModel):
    """A request to run a supported workload on a chosen worker."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)
    workload_type: Literal["sum_integers"]
    input_data: list[int] = Field(min_length=1, max_length=10_000)


class JobResultSubmission(BaseModel):
    """A worker's successful result or failure report."""

    model_config = ConfigDict(extra="forbid")

    result: int | None = None
    error: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_result_or_error(self) -> "JobResultSubmission":
        if (self.result is None) == (self.error is None):
            raise ValueError("Provide exactly one of result or error")
        return self


class JobRecord(BaseModel):
    """A job as tracked by the controller."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(default_factory=lambda: str(uuid4()))
    worker_id: str
    workload_type: Literal["sum_integers"]
    input_data: list[int]
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    result: int | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))