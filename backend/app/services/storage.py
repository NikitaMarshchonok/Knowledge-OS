from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile


def save_upload_file(file: UploadFile, base_storage_dir: str, project_id: UUID) -> tuple[str, str, int]:
    project_storage_dir = Path(base_storage_dir) / str(project_id)
    project_storage_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename or "").suffix
    filename = f"{uuid4()}{extension}"
    absolute_path = project_storage_dir / filename

    content = file.file.read()
    absolute_path.write_bytes(content)

    return filename, str(absolute_path), len(content)
