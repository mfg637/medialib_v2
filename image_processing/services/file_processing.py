from django.core.files.uploadedfile import UploadedFile
from image_processing.core.file_format import EXTENSIONS_BY_MIME
from image_processing.core.file_utils import (
    detect_file_type,
    generate_filename,
    MediaType,
)
from io import BytesIO
from pathlib import Path


def get_file_type(file: UploadedFile) -> tuple[str, MediaType]:
    header = file.read(2048)
    file.seek(0)
    return detect_file_type(BytesIO(header), file.content_type)


def normalize_or_create_filename(name: str | None, mime: str) -> str:
    valid_suffix = EXTENSIONS_BY_MIME.get(mime)
    if name:
        p = Path(name)
        if valid_suffix and p.suffix != valid_suffix:
            name = p.with_suffix(valid_suffix).name
    else:
        name = str(generate_filename(mime)[0])

    return name
