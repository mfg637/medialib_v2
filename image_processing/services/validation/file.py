from base.shared_knowledge.file_format import (
    ALLOWED_FILE_FORMATS,
    MIME_TYPE_TO_FORMAT,
)
from image_processing.core.file_utils import calc_sha256
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from medialib import models as ml_models
from pathlib import Path


def validate_media_format(mime: str) -> None:
    if MIME_TYPE_TO_FORMAT.get(mime) not in ALLOWED_FILE_FORMATS:
        raise ValidationError(f"File type {mime} not allowed")


def calc_hash_and_find(
    source_file: Path | UploadedFile,
) -> tuple[QuerySet, bytes]:
    if hasattr(source_file, "path"):
        source_file = source_file.path
    file_hash = calc_sha256(source_file)
    found_set = ml_models.Content.objects.filter(source_hash=file_hash)
    return found_set, file_hash


def prevent_duplication(
    source_file: UploadedFile, origin_name: str, origin_id: str
) -> bytes:
    found_set, file_hash = calc_hash_and_find(source_file)
    if found_set.exists():
        content = found_set.first()
        if origin_name and origin_id:
            ml_models.ContentOrigin.objects.get_or_create(
                content=content,
                name=origin_name,
                origin_id=origin_id,
                defaults={"alternate": True},
            )
        raise ValidationError("Duplicate file found")
    return file_hash
