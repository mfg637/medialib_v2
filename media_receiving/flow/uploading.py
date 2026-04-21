from media_receiving.services import file_processing, validation
from media_receiving.core.file import LocalFile
from django.core.files.uploadedfile import UploadedFile
from media_receiving.models import Task


def process_task_file(
    uploaded_file: UploadedFile | LocalFile,
    instance: Task,
    origin_name="",
    origin_id="",
) -> UploadedFile | LocalFile:
    mime, media_type = file_processing.get_file_type(uploaded_file)
    validation.validate_media_format(mime)
    instance.source_hash = validation.prevent_file_duplication(
        uploaded_file, origin_name, origin_id
    )

    instance.mime_type = mime
    instance.media_type = media_type

    uploaded_file.name = file_processing.normalize_or_create_filename(
        uploaded_file.name, mime
    )

    return uploaded_file
