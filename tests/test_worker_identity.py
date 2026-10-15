
from uuid import UUID

import pytest

from daballs.worker.identity import get_or_create_worker_id


def test_worker_id_is_created_and_reused(tmp_path) -> None:
    storage_path = tmp_path / ".daballs" / "worker_id"

    first_id = get_or_create_worker_id(storage_path)
    second_id = get_or_create_worker_id(storage_path)

    assert first_id == second_id
    assert storage_path.read_text(encoding="utf-8").strip() == first_id
    assert str(UUID(first_id)) == first_id


def test_invalid_saved_worker_id_is_rejected(tmp_path) -> None:
    storage_path = tmp_path / "worker_id"
    storage_path.write_text("not-a-valid-uuid", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid worker ID"):
        get_or_create_worker_id(storage_path)