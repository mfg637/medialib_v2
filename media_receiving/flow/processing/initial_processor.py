import logging
from typing import Type, TYPE_CHECKING

from django.apps import apps

from .base_processor import BaseTaskProcessor
from .exceptions import DiscardedProcessing

if TYPE_CHECKING:
    from medialib.models import (
        Content,
        ContentOrigin,
    )

logger = logging.getLogger(__name__)


class InitialTaskProcessor(BaseTaskProcessor):
    def get_or_create_content(self, task, passport, t_meta, task_file):
        ContentModel: Type[Content] = apps.get_model("medialib", "Content")

        title = t_meta.title if t_meta and t_meta.title else task_file.stem
        description = t_meta.description if t_meta else ""

        if not task.source_hash:
            raise ValueError(f"invalid source_hash in task {task.id}")
        existing_content = ContentModel.objects.filter(
            source_hash=task.source_hash
        )
        if existing_content.exists():
            task_file.unlink(missing_ok=True)
            task.uploaded_file = None
            task.save()
            if t_meta is not None:
                t_meta.delete()
            raise DiscardedProcessing("Content already exists")
        else:
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
