
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkerRegistration(BaseModel):
    """Hardware and resource information supplied by a worker."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)
    hostname: str = Field(min_length=1, max_length=255)
    os_name: str = Field(min_length=1, max_length=100)
    architecture: str = Field(min_length=1, max_length=100)

    cpu_logical_cores: int = Field(gt=0, le=4096)

    memory_total_bytes: int = Field(gt=0)
    memory_available_bytes: int = Field(ge=0)

    offered_cpu_cores: int = Field(ge=0, le=4096, default=0)
    offered_memory_bytes: int = Field(ge=0, default=0)


    @model_validator(mode="after")
    def validate_resources(self) -> "WorkerRegistration":
        if self.memory_available_bytes > self.memory_total_bytes:
            raise ValueError("Available memory cannot exceed total memory")

        if self.offered_cpu_cores > self.cpu_logical_cores:
            raise ValueError("Offered CPU cores cannot exceed logical CPU cores")

        if self.offered_memory_bytes > self.memory_total_bytes:
            raise ValueError("Offered memory cannot exceed total memory")

        return self


class WorkerRecord(WorkerRegistration):
    """Worker information maintained by the controller."""

    status: Literal["online", "offline"] = "online"
    registered_at: datetime
    last_seen_at: datetime
