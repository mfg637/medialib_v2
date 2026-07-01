import logging
from pathlib import Path
from typing import Optional, List, Type, TYPE_CHECKING
from abc import ABC, abstractmethod

from django.db import transaction
from django.conf import settings
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
        TaskResult,
    )
    from medialib.models import (
        Content,
        Representation as RepresentationModel,
        ImageHash,
    )

logger = logging.getLogger(__name__)


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


def discard_task(task: Task):
    task_file = Path(task.uploaded_file.path)
    task_file.unlink(missing_ok=True)
    task.uploaded_file = None
    task.save()
    if task.metadata is not None:
        task.metadata.delete()
