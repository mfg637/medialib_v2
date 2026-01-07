from image_processing.services import file_processing, validation
from django.core.files.uploadedfile import UploadedFile
from image_processing.models import Task


def process_task_file(
    uploaded_file: UploadedFile, instance: Task
) -> UploadedFile:
    mime, media_type = file_processing.get_file_type(uploaded_file)
    validation.validate_media_format(mime)

    instance.mime_type = mime
    instance.media_type = media_type

    uploaded_file.name = file_processing.normalize_or_create_filename(
        uploaded_file.name, mime
    )

    return uploaded_file
