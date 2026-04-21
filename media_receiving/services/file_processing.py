from media_receiving.core.file import LocalFile
from django.core.files.uploadedfile import UploadedFile
from base.shared_knowledge.file_format import EXTENSIONS_BY_MIME
from image_processing.core.file_utils import (
    detect_file_type,
    generate_filename,
    MediaType,
)
from media_receiving.config import MAX_FILE_LENGTH, TASK_SAVE_DIRECTORY
from io import BytesIO
from pathlib import Path

# add 1 character for "/"
DIRECTORY_NAME_LENGTH = len(str(TASK_SAVE_DIRECTORY)) + 1
DJANGO_UNIQUENESS_RESERVE = 8


def get_file_type(file: UploadedFile | LocalFile) -> tuple[str, MediaType]:
    header = file.read(2048)
    file.seek(0)
    return detect_file_type(BytesIO(header), file.content_type)


def normalize_or_create_filename(name: str | None, mime: str) -> str:
    valid_suffix = EXTENSIONS_BY_MIME.get(mime)
    if valid_suffix is not None:
        if name:
            p = Path(name)
            stem_length_limit = (
                MAX_FILE_LENGTH
                - len(valid_suffix)
                - DIRECTORY_NAME_LENGTH
                - DJANGO_UNIQUENESS_RESERVE
            )
            name = f"{p.stem[:stem_length_limit]}{valid_suffix}"
        else:
            name = str(generate_filename(mime)[0])
    else:
        raise ValueError(f"Unexpected mime type: {mime}")

    return name
