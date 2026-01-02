from io import BytesIO
from pathlib import Path
from django.contrib import admin
from .models import Task, AwaitingTaskMetadata
from django import forms
from medialib_v2.settings import MEDIALIB_ROOT
from image_processing.common.file_format import (
    EXTENSIONS_BY_MIME,
    ALLOWED_FILE_FORMATS,
    MIME_TYPE_TO_FORMAT,
)
from image_processing.common.file_utils import (
    detect_file_type,
)
from django.core.exceptions import ValidationError


class TaskUploadForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["uploaded_file"]

    def clean_uploaded_file(self):
        file = self.cleaned_data["uploaded_file"]

        header = file.read(2048)
        file.seek(0)
        mime, media_type = detect_file_type(BytesIO(header), file.content_type)

        if MIME_TYPE_TO_FORMAT.get(mime) not in ALLOWED_FILE_FORMATS:
            raise ValidationError(f"File type {mime} not allowed to upload")

        self.instance.mime_type = mime
        self.instance.media_type = media_type

        return file

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.instance.uploaded_file
        if uploaded_file:
            current_path = Path(uploaded_file.path)
            valid_suffix = EXTENSIONS_BY_MIME.get(self.instance.mime_type)

            if valid_suffix and current_path.suffix != valid_suffix:
                new_path = current_path.with_suffix(valid_suffix)

                current_path.rename(new_path)

                self.instance.uploaded_file.name = str(
                    new_path.relative_to(MEDIALIB_ROOT)
                )

        if commit:
            instance.save()

        return instance


class MetadataInline(admin.StackedInline):
    model = AwaitingTaskMetadata
    can_delete = False
    verbose_name_plural = "Metadata of Task"
    exclude = ["tags"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskUploadForm
    inlines = [MetadataInline]

    list_display = ("id", "status", "created_at")
    list_filter = ("status",)
