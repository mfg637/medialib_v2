from base.shared_knowledge.file_format import (
    ALLOWED_FILE_FORMATS,
    MIME_TYPE_TO_FORMAT,
)
from image_processing.core.file_utils import calc_sha256
from django.core.exceptions import ValidationError
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile


def validate_media_format(mime: str) -> None:
    if MIME_TYPE_TO_FORMAT.get(mime) not in ALLOWED_FILE_FORMATS:
        raise ValidationError(f"File type {mime} not allowed")


def check_is_unique(source_file: Path | UploadedFile) -> bool:
    from medialib.models import Content

    file_hash = calc_sha256(source_file)
    is_exists = Content.objects.filter(source_hash=file_hash).exists()
    return not is_exists


def prevent_duplication(source_file: UploadedFile) -> None:
    if not check_is_unique(source_file):
        raise ValidationError("Duplicate file found")
