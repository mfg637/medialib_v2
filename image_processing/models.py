import pathlib
from django.db import models
import enum


DEBUG = False


class TaskStatusEnum(enum.IntEnum):
    AWAITING = 0
    DONE = 1
    ERROR = 2


class Task(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_created=True)
    tmp_file = models.FilePathField(null=True)
    STATUS_LIST = [
        (TaskStatusEnum.AWAITING, "Wait for processing…"),
        (TaskStatusEnum.DONE, "Done!"),
        (TaskStatusEnum.ERROR, "ERROR!!!")
    ]
    status = models.IntegerField(choices=STATUS_LIST)


class TaskResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    source_file_size = models.PositiveBigIntegerField()
    result_file_size = models.PositiveBigIntegerField()
    quality = models.SmallIntegerField()
    lossless = models.BooleanField()


class ContentRepresentation(models.Model):
    id = models.BigAutoField(primary_key=True)
    content = models.ForeignKey(TaskResult, on_delete=models.CASCADE, db_index=True)
    filepath = models.FilePathField(
        unique=True,
        null=False
    )
    format = models.CharField(max_length=12)
    compatibility_level = models.PositiveSmallIntegerField(
        "Compatibility level",
    )

    def delete(self, *args, **kwargs):
        if not DEBUG:
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class ExecutionError(models.Model):
    id = models.BigAutoField(primary_key=True)
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    details = models.TextField(null=True)
