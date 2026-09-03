import uuid
from pathlib import Path

from fastapi import UploadFile

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "uploads"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB


async def save_submission_file(assignment_id: str, student_id: str, file: UploadFile) -> tuple[str, str]:
    """Saves an uploaded file and returns (original_filename, stored_relative_path)."""
    directory = UPLOAD_ROOT / assignment_id / student_id
    directory.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "").suffix[:20]
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = directory / stored_name

    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise ValueError("파일 크기는 20MB를 초과할 수 없습니다.")
            out.write(chunk)

    relative_path = str(dest.relative_to(UPLOAD_ROOT))
    return file.filename or stored_name, relative_path


def resolve_upload_path(relative_path: str) -> Path:
    path = (UPLOAD_ROOT / relative_path).resolve()
    if UPLOAD_ROOT.resolve() not in path.parents and path != UPLOAD_ROOT.resolve():
        raise ValueError("잘못된 파일 경로입니다.")
    return path
