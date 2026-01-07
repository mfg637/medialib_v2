from django.db import models
import enum

import medialib.models
from django.core.exceptions import ValidationError
from image_processing.core.file_utils import MediaType
from medialib_v2 import settings


class TaskStatusEnum(enum.IntEnum):
    AWAITING = 0
    DONE = 1
    ERROR = 2


class Task(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_file = models.FileField(
        upload_to=settings.MEDIALIB_QUEUE_DIRECTORY,
        null=True,
    )
    STATUS_LIST = [
        (TaskStatusEnum.AWAITING, "Wait for processing…"),
        (TaskStatusEnum.DONE, "Done!"),
        (TaskStatusEnum.ERROR, "ERROR!!!"),
    ]
    media_type = models.CharField(
        max_length=10, choices=MediaType, null=True, blank=True
    )
    mime_type = models.CharField(max_length=128, null=True, blank=True)
    status = models.IntegerField(
        choices=STATUS_LIST, default=TaskStatusEnum.AWAITING
    )

    def clean(self) -> None:
        if (
            self.status is not TaskStatusEnum.DONE
            and self.uploaded_file is None
        ):
            raise ValidationError(
                "Temporary file can not be None until process is done"
            )
        return super().clean()

    # def save(self, *args, **kwargs):
    #     self.full_clean()
    #     super().save(*args, **kwargs)


class AwaitingTaskMetadata(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    origin_name = models.CharField(max_length=32, null=True, blank=True)
    origin_id = models.CharField(max_length=512, null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
    task = models.OneToOneField(Task, on_delete=models.CASCADE)


class TaskResult(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    # should be reference to content, if content exists
    content = models.ForeignKey(
        medialib.models.Content, null=True, on_delete=models.SET_NULL
    )
    # file size fields can be only used for statistic purposes
    # file size savings were deprioritized in favor to shorten response delay
    source_file_size = models.PositiveBigIntegerField()
    result_file_size = models.PositiveBigIntegerField()
    # quality became constant number, depending on representation size and type


class ExecutionError(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    title = models.TextField(help_text="The name of the error")
    details = models.TextField(
        null=True,
        help_text=(
            "Detailed description of error. "
            "Likely to be exception stack trace"
        ),
    )
