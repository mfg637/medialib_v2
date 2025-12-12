from django.db import models
import enum
import medialib.models


class TaskStatusEnum(enum.IntEnum):
    AWAITING = 0
    DONE = 1
    ERROR = 2


class Task(models.Model):
    created_at = models.DateTimeField(auto_created=True)
    tmp_file = models.FilePathField(null=True)
    STATUS_LIST = [
        (TaskStatusEnum.AWAITING, "Wait for processing…"),
        (TaskStatusEnum.DONE, "Done!"),
        (TaskStatusEnum.ERROR, "ERROR!!!"),
    ]
    status = models.IntegerField(choices=STATUS_LIST)


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
