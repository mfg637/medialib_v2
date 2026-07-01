import traceback
import logging
import dataclasses
from typing import Type, TYPE_CHECKING


from celery import shared_task
from django.contrib.admin import action
from django.db.models import QuerySet
from django.apps import apps

from .base_processor import BaseTaskProcessor

if TYPE_CHECKING:
    from media_receiving.models import (
        Task,
    )
    from medialib.models import (
        Content,
        ImageHash,
        ContentOrigin,
        ContentRedirect,
    )

logger = logging.getLogger(__name__)


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
