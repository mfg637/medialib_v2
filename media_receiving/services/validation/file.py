from pathlib import Path
from typing import Optional
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.core.files.uploadedfile import UploadedFile
from base.shared_knowledge.file_format import (
    ALLOWED_FILE_FORMATS,
    MIME_TYPE_TO_FORMAT,
)
from image_processing.core.file_utils import calc_sha256
from medialib import models as ml_models
from media_receiving.core.file import LocalFile


def validate_media_format(mime: str) -> None:
    if MIME_TYPE_TO_FORMAT.get(mime) not in ALLOWED_FILE_FORMATS:
        raise ValidationError(f"File type {mime} not allowed")


def validate_file_not_empty(value: Path | UploadedFile | str):
    """
    Validates that an uploaded file or file path is not empty using pathlib.
    """
    if hasattr(value, "size"):
        if value.size == 0:
            raise ValidationError(
                _("The file '%(name)s' cannot be empty."),
                params={"name": file_path.name},
            )
    else:
        file_path: Path = (
            Path(value.path) if hasattr(value, "path") else Path(value)
        )

        if not file_path.exists():
            raise ValidationError(
                _("The file at '%(path)s' does not exist."),
                params={"path": file_path},
            )

        if not file_path.is_file():
            raise ValidationError(
                _("'%(path)s' is not a valid file."),
                params={"path": file_path},
            )

        if file_path.stat().st_size == 0:
            raise ValidationError(
                _("The file '%(name)s' cannot be empty."),
                params={"name": file_path.name},
            )


def calc_hash_and_find(
    source_file: Path | UploadedFile | LocalFile,
) -> tuple[
    QuerySet[ml_models.Content], Optional[ml_models.ContentRedirect], bytes
]:
    file_hash = calc_sha256(source_file)
    content_set = ml_models.Content.objects.filter(source_hash=file_hash)
    redirect_obj = ml_models.ContentRedirect.objects.filter(
        source_hash=file_hash
    ).first()
    return content_set, redirect_obj, file_hash


def prevent_duplication(
    source_file: UploadedFile | LocalFile, origin_name: str, origin_id: str
) -> bytes:
    content_set, redirect_obj, file_hash = calc_hash_and_find(source_file)
    target_content: Optional[ml_models.Content] = None

    if content_set.exists():
        target_content = content_set.first()
    elif redirect_obj:
        target_content = redirect_obj.new_content

    if target_content:
        if origin_name and origin_id:
            ml_models.ContentOrigin.objects.get_or_create(
                content=target_content,
                name=origin_name,
                origin_id=origin_id,
                defaults={"alternate": True},
            )
        raise ValidationError("Duplicate file found (original or merged)")

    return file_hash
