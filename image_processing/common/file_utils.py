import logging
import random
import string
import pathlib
import magic
import io
from django.db.models import TextChoices
from .file_format import (
    EXTENSIONS_BY_MIME,
    FormatEnum,
    MIME_TYPE_BY_FORMAT,
    GENERIC_BINARY_FILE_MIME,
    is_png,
)


logger = logging.getLogger(__name__)


def generate_filename(
    mime: str | None = None, *, extension: str | None = None
) -> tuple[pathlib.Path, str, str]:
    if extension is None:
        if mime is None:
            raise ValueError("At least one argument must be not None")
        extension = EXTENSIONS_BY_MIME[mime]
    title_only = "".join(
        random.choices(string.ascii_letters + string.digits, k=16)
    )
    return (
        pathlib.Path(title_only).with_suffix(extension),
        title_only,
        extension,
    )


def extract_filename(file_path: pathlib.Path | str):
    # return str(pathlib.Path(file_path).stem[: definitions.MAX_TITLE_LENGTH])
    return str(pathlib.Path(file_path).stem)


class MediaType(TextChoices):
    IMAGE = "image", "Image"
    AUDIO = "audio", "Audio"
    VIDEO = "video", "Video"


def detect_file_type(
    file_related: io.BytesIO | pathlib.Path, request_header_mimetype
) -> tuple[str, MediaType]:
    if isinstance(file_related, io.BytesIO):
        mime = magic.from_buffer(file_related.getvalue(), mime=True)
    elif isinstance(file_related, pathlib.Path):
        mime = magic.from_file(file_related, mime=True)
    if (
        mime is MIME_TYPE_BY_FORMAT[FormatEnum.MOV]
        and request_header_mimetype is MIME_TYPE_BY_FORMAT[FormatEnum.MPEG_4]
    ):
        mime = MIME_TYPE_BY_FORMAT[FormatEnum.MPEG_4]
    if mime is GENERIC_BINARY_FILE_MIME:
        if isinstance(file_related, io.BytesIO):
            file_related.seek(0)
            if is_png(file_related):
                mime = MIME_TYPE_BY_FORMAT[FormatEnum.PNG]
        elif isinstance(file_related, pathlib.Path):
            if is_png(file_related):
                mime = MIME_TYPE_BY_FORMAT[FormatEnum.PNG]
    if mime.startswith("image/"):
        file_type = MediaType.IMAGE
    elif mime.startswith("video/"):
        file_type = MediaType.VIDEO
    elif mime.startswith("audio/"):
        file_type = MediaType.AUDIO
    else:
        logger.error(f"undetected content type, mime: {mime}")
        raise Exception("undetected content type")
    return mime, file_type
