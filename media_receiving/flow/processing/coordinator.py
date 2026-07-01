import traceback
import logging
import dataclasses
from typing import Type, TYPE_CHECKING

from celery import shared_task
from django.apps import apps
from django.contrib.admin import action

from base.shared_enums.media_receiving_model import TaskStatusEnum
from .exceptions import DiscardedProcessing
from .base_processor import discard_task
from .initial_processor import InitialTaskProcessor
from .rewriting_processor import ContentRewritingProcessor

if TYPE_CHECKING:
    from media_receiving.models import (
        Task,
        TaskStatusEnum,
        ExecutionError,
    )
    from medialib.models import (
        Content,
    )

logger = logging.getLogger(__name__)


@shared_task
def process_task(task_id: int):
    TaskModel: Type[Task] = apps.get_model("media_receiving", "Task")
    ExecutionErrorModel: Type[ExecutionError] = apps.get_model(
        "media_receiving", "ExecutionError"
    )
    ContentModel: Type[Content] = apps.get_model("medialib", "Content")

    try:
        task = TaskModel.objects.get(id=task_id)
        initial_processor = InitialTaskProcessor(task)
        if task.rewrite:
            found_content = ContentModel.objects.filter(
                source_hash=task.source_hash
            ).first()
            if found_content is not None:
                rewriting_processor = ContentRewritingProcessor(
                    task, found_content
                )
                rewriting_processor.process_task()
            else:
                initial_processor.process_task()
        else:
            initial_processor.process_task()
    except DiscardedProcessing as e:
        TaskModel.objects.filter(id=task_id).update(
            status=TaskStatusEnum.DISCARDED
        )

        logger.warning("Discarded processing with exception: %s", e)
    except Exception as e:
        TaskModel.objects.filter(id=task_id).update(
            status=TaskStatusEnum.ERROR
        )

        ExecutionErrorModel.objects.create(
            task_id=task_id,
            title=f"{type(e).__name__}: {str(e)}",
            details=traceback.format_exc(),
        )
        raise e


@dataclasses.dataclass(frozen=True)
class TaskOrigin:
    name: str
    origin_id: str


@action()
def run_processing_selected_tasks(modeladmin, request, queryset):
    from media_receiving.models import (
        TaskStatusEnum,
    )

    pending_tasks = queryset.filter(
        status__in=[TaskStatusEnum.AWAITING, TaskStatusEnum.ERROR]
    )
    task_origins: set[TaskOrigin] = set()
    for task in pending_tasks:
        current_task_origin = None
        discarded = False
        if task.metadata.origin_name and task.metadata.origin_id:
            current_task_origin = TaskOrigin(
                task.metadata.origin_name, task.metadata.origin_id
            )
            if current_task_origin in task_origins:
                discarded = True
                task.status = TaskStatusEnum.DISCARDED
                discard_task(task)
            else:
                task_origins.add(current_task_origin)
        if not discarded:
            process_task.delay(task.id)
            task.status = TaskStatusEnum.PROCESSING
            task.save()
    modeladmin.message_user(
        request, f"Launched tasks: {pending_tasks.count()}"
    )
