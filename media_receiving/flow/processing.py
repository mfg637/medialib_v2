import traceback
from pathlib import Path
from typing import Optional, List, Type, TYPE_CHECKING
from abc import ABC, abstractmethod

from django.db import transaction
from django.conf import settings
from celery import shared_task
from django.contrib.admin import action
from django.db.models import QuerySet
from django.apps import apps

from base.shared_knowledge.file_format import FILE_FORMAT_DEFAULT_SUFFIX
from base.shared_enums.media_receiving_model import TaskStatusEnum
from image_processing.services import analysis, media_passport
from media_receiving.services.storage import move_representations
from media_receiving.services.tags_processing import process_content_tags
from image_processing.services.representations import (
    make_representations,
    get_image_signatures,
    Representation,
)

if TYPE_CHECKING:
    from media_receiving.models import (
        Task,
        AwaitingTaskMetadata,
        TaskStatusEnum,
        TaskResult,
        ExecutionError,
    )
    from medialib.models import (
        Content,
        Representation as RepresentationModel,
        ImageHash,
        ContentOrigin,
        ContentRedirect,
    )


class BaseTaskProcessor(ABC):
    def __init__(self, task: Task):
        self.task = task
        self.content = None

    @abstractmethod
    def get_or_create_content(
        self,
        task: Task,
        passport: media_passport.BaseMediaPassport,
        t_meta: Optional[AwaitingTaskMetadata],
        task_file,
    ) -> Content:
        pass

    @abstractmethod
    def manage_origins(
        self, content: Content, t_meta: Optional[AwaitingTaskMetadata]
    ):
        pass

    def before_moving_representations(self, content: Content):
        pass

    def process_task(self):
        AwaitingTaskMetadataModel: Type[AwaitingTaskMetadata] = apps.get_model(
            "media_receiving", "AwaitingTaskMetadata"
        )
        ImageHashModel: Type[ImageHash] = apps.get_model(
            "medialib", "ImageHash"
        )
        RepresentationModelType: Type[RepresentationModel] = apps.get_model(
            "medialib", "Representation"
        )
        TaskResultModel: Type[TaskResult] = apps.get_model(
            "media_receiving", "TaskResult"
        )

        source_size = 0
        task = self.task
        with transaction.atomic():
            if task.status == TaskStatusEnum.DONE.value:
                return
            source_size = task.uploaded_file.size

            if source_size == 0:
                raise ValueError("Task file is empty")

            passport, comp_level = analysis.do_analysis(
                task.uploaded_file, task.mime_type, task.media_type
            )
            task_file = passport.source_file

            t_meta: Optional[AwaitingTaskMetadata] = (
                AwaitingTaskMetadataModel.objects.filter(
                    task_id=task.id
                ).first()
            )

            content: Content = self.get_or_create_content(
                task, passport, t_meta, task_file
            )

            if t_meta and t_meta.tags:
                process_content_tags(content, t_meta.tags)

            self.manage_origins(content, t_meta)

            repr_list: List[Representation] = make_representations(
                passport, comp_level
            )
            if isinstance(passport, media_passport.StaticImagePassport):
                sig = get_image_signatures(passport)
                ImageHashModel.objects.create(
                    content=content,
                    aspect_ratio=sig.aspect_ratio,
                    L_hash=sig.l_hash,
                    a_hash=sig.a_hash,
                    b_hash=sig.b_hash,
                )

            self.before_moving_representations(content)
            repr_list = move_representations(content, repr_list)

            total_result_size = 0
            for r in repr_list:
                abs_path = Path(settings.MEDIA_ROOT) / r.file_path
                total_result_size += abs_path.stat().st_size
                codec_string = ""
                if r.codec_string:
                    codec_string = r.codec_string

                RepresentationModelType.objects.create(
                    content=content,
                    filepath=str(r.file_path),
                    format=FILE_FORMAT_DEFAULT_SUFFIX[r._format].lstrip("."),
                    width=r.width,
                    height=r.height,
                    compatibility_level=r.compatibility_level,
                    codec_string=codec_string,
                    repr_type=r.repr_type,
                    hash=r.repr_hash,
                )

            TaskResultModel.objects.create(
                task=task,
                content=content,
                source_file_size=source_size,
                result_file_size=total_result_size,
            )

            task.status = TaskStatusEnum.DONE.value
            task_file.unlink(missing_ok=True)
            task.uploaded_file = None
            task.save()

            if t_meta is not None:
                t_meta.delete()


class InitialTaskProcessor(BaseTaskProcessor):
    def get_or_create_content(self, task, passport, t_meta, task_file):
        ContentModel: Type[Content] = apps.get_model("medialib", "Content")

        title = t_meta.title if t_meta and t_meta.title else task_file.stem
        description = t_meta.description if t_meta else ""

        if not task.source_hash:
            raise ValueError(f"invalid source_hash in task {task.id}")
        return ContentModel.objects.create(
            title=title,
            description=description,
            content_type=passport.content_type,
            source_hash=task.source_hash,
        )

    def manage_origins(self, content, t_meta):
        ContentOriginModel: Type[ContentOrigin] = apps.get_model(
            "medialib", "ContentOrigin"
        )

        if t_meta and t_meta.origin_name:
            ContentOriginModel.objects.create(
                content=content,
                name=t_meta.origin_name,
                origin_id=t_meta.origin_id,
            )


class ContentRewritingProcessor(BaseTaskProcessor):
    def __init__(self, task: Task, content):
        super().__init__(task)
        self.content = content

    def get_or_create_content(self, task, passport, t_meta, task_file):
        ImageHashModel: Type[ImageHash] = apps.get_model(
            "medialib", "ImageHash"
        )
        ContentRedirectModel: Type[ContentRedirect] = apps.get_model(
            "medialib", "ContentRedirect"
        )

        content: Content = self.content
        content.content_type = passport.content_type
        ImageHashModel.objects.filter(content=content).delete()

        if self.content.source_hash.tobytes() != task.source_hash.tobytes():
            ContentRedirectModel.objects.create(
                old_slug=content.slug,
                new_content=content,
                created_at=content.addition_date,
                source_hash=content.source_hash,
            )
            content.source_hash = task.source_hash
            content.slug = content.generate_slug()

        content.save()
        return content

    def manage_origins(self, content, t_meta):
        current_origin_name = t_meta.origin_name if t_meta else ""
        current_origin_id = t_meta.origin_id if t_meta else ""
        if current_origin_name:
            main_origin_old: QuerySet[ContentOrigin] = (
                content.origin_set.filter(alternate=False).exclude(
                    name=current_origin_name, origin_id=current_origin_id
                )
            )
            main_origin_old.update(alternate=True)
            main_origin, created = content.origin_set.get_or_create(
                name=current_origin_name,
                origin_id=current_origin_id,
                defaults={"alternate": False},
            )
            if not created and main_origin.alternate:
                main_origin.alternate = False
                main_origin.save()

    def before_moving_representations(self, content):
        old_representations = content.representation_set.all()
        for old_repr in old_representations:
            if old_repr.filepath:
                old_repr.filepath.delete(save=False)
            old_repr.delete()


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


@action()
def run_processing_selected_tasks(modeladmin, request, queryset):
    from media_receiving.models import (
        TaskStatusEnum,
    )

    pending_tasks = queryset.filter(
        status__in=[TaskStatusEnum.AWAITING, TaskStatusEnum.ERROR]
    )
    for task in pending_tasks:
        process_task.delay(task.id)
        task.status = TaskStatusEnum.PROCESSING
        task.save()
    modeladmin.message_user(
        request, f"Launched tasks: {pending_tasks.count()}"
    )
