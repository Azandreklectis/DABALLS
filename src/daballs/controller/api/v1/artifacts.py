from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse

from daballs.workloads.artifact_store import (
    ArtifactMetadata,
    artifact_store,
)
from daballs.workloads.package_validator import (
    MAX_ARCHIVE_BYTES,
    WorkloadPackageError,
)

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactMetadata, status_code=status.HTTP_201_CREATED)
async def upload_artifact(request: Request) -> ArtifactMetadata:
    content_type = request.headers.get("content-type", "").split(";")[0].strip()

    if content_type != "application/zip":
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be application/zip",
        )

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid Content-Length header",
            ) from exc

        if declared_length < 0 or declared_length > MAX_ARCHIVE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Archive exceeds the 50 MiB limit",
            )

    chunks: list[bytes] = []
    total_bytes = 0

    async for chunk in request.stream():
        total_bytes += len(chunk)
        if total_bytes > MAX_ARCHIVE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Archive exceeds the 50 MiB limit",
            )
        chunks.append(chunk)

    try:
        return artifact_store.save(b"".join(chunks))
    except WorkloadPackageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{artifact_id}/metadata", response_model=ArtifactMetadata)
def get_artifact_metadata(artifact_id: str) -> ArtifactMetadata:
    try:
        metadata = artifact_store.get_metadata(artifact_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkloadPackageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if metadata is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return metadata


@router.get("/{artifact_id}")
def download_artifact(artifact_id: str) -> Response:
    try:
        path = artifact_store.get_path(artifact_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkloadPackageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if path is None:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return FileResponse(
        path,
        media_type="application/zip",
        filename=f"{artifact_id}.zip",
    )