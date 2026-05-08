from pathlib import Path
from uuid import uuid4


def build_storage_path(base_dir: Path, original_filename: str) -> tuple[str, Path]:
    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{suffix}"
    return stored_filename, base_dir / stored_filename
