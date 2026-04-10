from django.db import models
import enum

from medialib.models import Content
from django.core.exceptions import ValidationError
from base.view import format_file_size
from base.shared_knowledge.origin import get_origin_type
from base.shared_enums.image_processing_model import MediaType
from image_processing.config import TASK_SAVE_DIRECTORY, MAX_FILE_LENGTH


class TaskStatusEnum(enum.IntEnum):
    AWAITING = 0
    DONE = 1
    ERROR = 2
    PROCESSING = 3


class Task(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_file = models.FileField(
        upload_to=TASK_SAVE_DIRECTORY,
        null=True,
        max_length=MAX_FILE_LENGTH,
    )
    STATUS_LIST = [
        (TaskStatusEnum.AWAITING, "Wait for processing…"),
        (TaskStatusEnum.DONE, "Done!"),
        (TaskStatusEnum.ERROR, "ERROR!!!"),
        (TaskStatusEnum.PROCESSING, "Processing…"),
    ]
    media_type = models.CharField(
        max_length=10, choices=MediaType, null=True, blank=True
    )
    mime_type = models.CharField(max_length=128, null=True, blank=True)
    source_hash = models.BinaryField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of the original file content (stored as BYTEA).",
    )
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

    def get_status_display(self) -> str:
        return self.STATUS_LIST[self.status][1]

    def __str__(self):
        if self.uploaded_file:
            return (
                f"Task {self.id} "
                f"[{self.get_status_display()}] - "
                f"{self.uploaded_file.name}"
            )
        else:
            return f"Task {self.id} " f"[{self.get_status_display()}] - "


class AwaitingTaskMetadata(models.Model):
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    origin_name = models.CharField(max_length=32, blank=True, default="")
    origin_id = models.CharField(max_length=512, blank=True, default="")
    tags = models.JSONField(null=True, blank=True)
    task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name="metadata"
    )

    def save(self, *args, **kwargs):
        if self.origin_id and self.origin_id.startswith("https://"):
            try:
                origin_class = get_origin_type(self.origin_name)
                if origin_class:
                    origin_object = origin_class()
                    parsed_id = origin_object.parse_url(self.origin_id)

                    self.origin_id = parsed_id or ""
            except ValueError, KeyError:
                self.origin_id = ""

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            "AwaitingTaskMetadata "
            f"task id: {self.task.id}, "
            f"title={self.title}, "
            f"origin: name={self.origin_name}, id={self.origin_id}, "
            f"tags: {str(self.tags)}"
        )


class TaskResult(models.Model):
    task = models.OneToOneField(
        Task, on_delete=models.CASCADE, related_name="result"
    )
    # should be reference to content, if content exists
    content = models.ForeignKey(
        Content,
        null=True,
        on_delete=models.SET_NULL,
        related_name="task_results",
    )
    # file size fields can be only used for statistic purposes
    # file size savings were deprioritized in favor to shorten response delay
    source_file_size = models.PositiveBigIntegerField()
    result_file_size = models.PositiveBigIntegerField()
    # quality became constant number, depending on representation size and type

    def __str__(self):
        if self.content is not None:
            return (
                "TaskResult "
                f"task id: {self.task.id}, "
                f"content id: {self.content.id} "
                f"source_file_size = {format_file_size(self.source_file_size)}, "
                f"result_file_size = {format_file_size(self.result_file_size)}, "
            )
        else:
            return (
                "TaskResult "
                f"task id: {self.task.id}, "
                f"source_file_size = {format_file_size(self.source_file_size)}, "
                f"result_file_size = {format_file_size(self.result_file_size)}, "
            )


class ExecutionError(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="errors"
    )
    title = models.TextField(help_text="The name of the error")
    details = models.TextField(
        blank=True,
        help_text=(
            "Detailed description of error. "
            "Likely to be exception stack trace"
        ),
        default="",
    )

    def __str__(self):
        return f"ExecutionError task id: {self.task.id}, title: {self.title}"
