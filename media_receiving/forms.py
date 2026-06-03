from django import forms
from django.core.files.uploadedfile import UploadedFile
from typing import Optional
from media_receiving.flow.uploading import process_task_file
from django.core.exceptions import ValidationError
from .models import Task


class TaskUploadForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["uploaded_file", "rewrite"]

    def clean_uploaded_file(self) -> UploadedFile:
        file: Optional[UploadedFile] = self.cleaned_data.get("uploaded_file")
        instance: Task = self.instance

        if file is None:
            raise ValidationError("Uploaded file must not be None")

        return process_task_file(file, instance)
