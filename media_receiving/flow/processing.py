import traceback
from pathlib import Path
from typing import Optional, List
from django.db import transaction
from django.conf import settings
from celery import shared_task
from django.contrib.admin import action
from django.db.models import QuerySet

from base.shared_knowledge.file_format import FILE_FORMAT_DEFAULT_SUFFIX
from image_processing.services import analysis, media_passport
from media_receiving.services.storage import move_representations
from media_receiving.services.tags_processing import process_content_tags
from image_processing.services.representations import (
    make_representations,
    get_image_signatures,
    Representation,
)
from media_receiving.models import (
    Task,
    AwaitingTaskMetadata,
    TaskStatusEnum,
    TaskResult,
    ExecutionError,
)


def initial_task_processing(task: Task):
    from medialib.models import (
        Content,
        Representation as RepresentationModel,
        ContentOrigin,
        ImageHash,
    )

    source_size = 0
    with transaction.atomic():
        if task.status == TaskStatusEnum.DONE.value:
            return
        source_size = task.uploaded_file.size

        passport, comp_level = analysis.do_analysis(
            task.uploaded_file, task.mime_type, task.media_type
        )
        task_file = passport.source_file

        t_meta: Optional[AwaitingTaskMetadata] = (
            AwaitingTaskMetadata.objects.filter(task_id=task.id).first()
        )
        title = t_meta.title if t_meta and t_meta.title else task_file.stem
        description = t_meta.description if t_meta else ""

        if not task.source_hash:
            raise ValueError(f"invalid source_hash in task {task_id}")
        content = Content.objects.create(
            title=title,
            description=description,
            content_type=passport.content_type,
            source_hash=task.source_hash,
        )

        if t_meta and t_meta.tags:
            process_content_tags(content, t_meta.tags)

        if t_meta and t_meta.origin_name:
            ContentOrigin.objects.create(
                content=content,
                name=t_meta.origin_name,
                origin_id=t_meta.origin_id,
            )

        repr_list: List[Representation] = make_representations(
            passport, comp_level
        )
        if isinstance(passport, media_passport.StaticImagePassport):
            sig = get_image_signatures(passport)
            ImageHash.objects.create(
                content=content,
                aspect_ratio=sig.aspect_ratio,
                L_hash=sig.l_hash,
                a_hash=sig.a_hash,
                b_hash=sig.b_hash,
            )
        repr_list = move_representations(content, repr_list)

        total_result_size = 0
        for r in repr_list:
            abs_path = Path(settings.MEDIA_ROOT) / r.file_path
            total_result_size += abs_path.stat().st_size
            codec_string = ""
            if r.codec_string:
                codec_string = r.codec_string

            RepresentationModel.objects.create(
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

        TaskResult.objects.create(
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


def task_rewrite_processing(task: Task, content):
    from medialib.models import (
        Content,
        Representation as RepresentationModel,
        ContentOrigin,
        ContentRedirect,
        ImageHash,
    )

    source_size = 0
    if not isinstance(content, Content):
        raise TypeError(
            "Content argument must have type medialib.models.Content"
        )
    with transaction.atomic():
        if task.status == TaskStatusEnum.DONE.value:
            return
        source_size = task.uploaded_file.size

        passport, comp_level = analysis.do_analysis(
            task.uploaded_file, task.mime_type, task.media_type
        )
        task_file = passport.source_file

        t_meta: Optional[AwaitingTaskMetadata] = (
            AwaitingTaskMetadata.objects.filter(task_id=task.id).first()
        )

        if not task.source_hash:
            raise ValueError(f"invalid source_hash in task {task.id}")

        content.content_type = passport.content_type
        ImageHash.objects.filter(content=content).delete()

        if content.source_hash.tobytes() != task.source_hash.tobytes():
            ContentRedirect.objects.create(
                old_slug=content.slug,
                new_content=content,
                created_at=content.addition_date,
                source_hash=content.source_hash,
            )
            content.source_hash = task.source_hash
            content.slug = content.generate_slug()

        content.save()

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

        # internal methods using duplicate-safe operations,
        # like .add() or get_or_create()
        if t_meta and t_meta.tags:
            process_content_tags(content, t_meta.tags)

        repr_list: List[Representation] = make_representations(
            passport, comp_level
        )
        if isinstance(passport, media_passport.StaticImagePassport):
            sig = get_image_signatures(passport)
            ImageHash.objects.create(
                content=content,
                aspect_ratio=sig.aspect_ratio,
                L_hash=sig.l_hash,
                a_hash=sig.a_hash,
                b_hash=sig.b_hash,
            )

        old_representations = content.representation_set.all()
        for old_repr in old_representations:
            if old_repr.filepath:
                old_repr.filepath.delete(save=False)
            old_repr.delete()

        repr_list = move_representations(content, repr_list)

        total_result_size = 0
        for r in repr_list:
            abs_path = Path(settings.MEDIA_ROOT) / r.file_path
            total_result_size += abs_path.stat().st_size
            codec_string = ""
            if r.codec_string:
                codec_string = r.codec_string

            RepresentationModel.objects.create(
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

        TaskResult.objects.create(
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


@shared_task
def process_task(task_id: int):
    from medialib.models import (
        Content,
    )

    try:
        # removed objects.select_for_update()
        task = Task.objects.get(id=task_id)
        if task.rewrite:
            found_content = Content.objects.filter(
                source_hash=task.source_hash
            ).first()
            if found_content is not None:
                task_rewrite_processing(task, found_content)
            else:
                initial_task_processing(task)
        else:
            initial_task_processing(task)

    except Exception as e:
        Task.objects.filter(id=task_id).update(status=TaskStatusEnum.ERROR)

        ExecutionError.objects.create(
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
