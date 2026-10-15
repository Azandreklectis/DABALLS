
from pathlib import Path
from uuid import UUID, uuid4


def get_or_create_worker_id(storage_path: Path | None = None) -> str:
    """Return a persistent worker ID, creating one on first use."""
    path = (
        storage_path
        if storage_path is not None
        else Path.home() / ".daballs" / "worker_id"
    )

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("x", encoding="utf-8") as file:
            worker_id = str(uuid4())
            file.write(worker_id + "\n")
            return worker_id
    except FileExistsError:
        worker_id = path.read_text(encoding="utf-8").strip()

    try:
        return str(UUID(worker_id))
    except ValueError as exc:
        raise ValueError(f"Invalid worker ID stored at {path}") from exc