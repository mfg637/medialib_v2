from django.contrib import admin
from .models import Task, AwaitingTaskMetadata
from django import forms
from django.core.files.uploadedfile import UploadedFile
from typing import Optional
from image_processing.flow.uploading import process_task_file
from django.core.exceptions import ValidationError


class TaskUploadForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["uploaded_file"]

    def clean_uploaded_file(self) -> UploadedFile:
        file: Optional[UploadedFile] = self.cleaned_data.get("uploaded_file")
        instance: Task = self.instance

        if file is None:
            raise ValidationError("Uploaded file must not be None")

        return process_task_file(file, instance)


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
