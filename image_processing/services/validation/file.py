from base.shared_knowledge.file_format import (
    ALLOWED_FILE_FORMATS,
    MIME_TYPE_TO_FORMAT,
)
from image_processing.core.file_utils import calc_sha256
from django.core.exceptions import ValidationError
from pathlib import Path


def validate_media_format(mime: str) -> None:
    if MIME_TYPE_TO_FORMAT.get(mime) not in ALLOWED_FILE_FORMATS:
        raise ValidationError(f"File type {mime} not allowed")


def check_is_unique(source_file: Path | UploadedFile) -> tuple[bool, bytes]:
    from medialib.models import Content

    if hasattr(source_file, "path"):
        source_file = source_file.path
    file_hash = calc_sha256(source_file)
    is_exists = Content.objects.filter(source_hash=file_hash).exists()
    return not is_exists, file_hash


def prevent_duplication(source_file: UploadedFile) -> bytes:
    is_unique, file_hash = check_is_unique(source_file)
    if not is_unique:
        raise ValidationError("Duplicate file found")
    return file_hash
