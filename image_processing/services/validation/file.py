from image_processing.core.file_format import (
    ALLOWED_FILE_FORMATS,
    MIME_TYPE_TO_FORMAT,
)
from django.core.exceptions import ValidationError


def validate_media_format(mime: str) -> None:
    if MIME_TYPE_TO_FORMAT.get(mime) not in ALLOWED_FILE_FORMATS:
        raise ValidationError(f"File type {mime} not allowed")
