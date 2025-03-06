from django.db import models
from medialib.models import Content
import enum


class TaskStatusEnum(enum.IntEnum):
    PROCESSING = 0
    DONE = 1
    ERROR = 2


class Task(models.Model):
    id = models.BigAutoField(primary_key=True)
    content = models.ForeignKey(Content, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_created=True)
    tmp_file = models.FileField(null=True)
    STATUS_LIST = [
        (TaskStatusEnum.PROCESSING, "Processing…"),
        (TaskStatusEnum.DONE, "Done!"),
        (TaskStatusEnum.ERROR, "ERROR!!!")
    ]
    status = models.IntegerField(choices=STATUS_LIST)


class TaskResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    source_file_size = models.PositiveBigIntegerField()
    result_file_size = models.PositiveBigIntegerField()
    quality = models.SmallIntegerField()
    lossless = models.BooleanField()


class ExecutionError(models.Model):
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    details = models.TextField(null=True)
