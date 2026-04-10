import json
import traceback
import logging
from pathlib import Path
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.core.files import File

from base.shared_knowledge.file_format import GENERIC_BINARY_FILE_MIME
from base.shared_enums.medialib_model import CategoryEnum
from media_receiving.flow.uploading import process_task_file
from medialib import models as ml_models
from .models import Task, AwaitingTaskMetadata, TaskStatusEnum
from .forms import TaskUploadForm

logger = logging.getLogger(__name__)


@csrf_exempt
def create_task_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    metadata_raw = request.POST.get("metadata")
    if metadata_raw:
        try:
            metadata_payload = json.loads(metadata_raw)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON in metadata field"}, status=400
            )
    else:
        metadata_payload = {
            "title": request.POST.get("title", ""),
            "description": request.POST.get("description", ""),
            "origin_name": request.POST.get("origin_name", ""),
            "origin_id": request.POST.get("origin_id", ""),
            "tags": request.POST.get("tags"),
        }

    form = TaskUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    try:
        with transaction.atomic():
            task = form.save()

            tags_data = metadata_payload.get("tags")
            if isinstance(tags_data, str):
                try:
                    tags_data = json.loads(tags_data)
                except json.JSONDecodeError:
                    pass

            AwaitingTaskMetadata.objects.create(
                task=task,
                title=metadata_payload.get("title", ""),
                description=metadata_payload.get("description", ""),
                origin_name=metadata_payload.get("origin_name", ""),
                origin_id=metadata_payload.get("origin_id", ""),
                tags=tags_data,
            )

            return JsonResponse(
                {
                    "task_id": task.id,
                    "status": task.get_status_display(),
                    "source_hash": (
                        task.source_hash.hex() if task.source_hash else None
                    ),
                    "mime_type": task.mime_type,
                },
                status=201,
            )

    except ValidationError as e:
        return JsonResponse(
            {"error": str(e.message if hasattr(e, "message") else e)},
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Internal server error", "details": str(e)}, status=500
        )


@csrf_exempt
def create_task_from_local_file(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    raw_path = request.POST.get("file_path", "")
    logger.debug("raw_path: %s", raw_path)
    if not raw_path:
        return JsonResponse({"error": "No file_path provided"}, status=400)

    full_path = Path(raw_path)

    logger.debug("full path '%s'", full_path)
    if not full_path.exists():
        return JsonResponse(
            {"error": f"File not found: {full_path}"}, status=404
        )

    try:
        tags = json.loads(request.POST.get("tags"))
        origin_name = request.POST.get("origin_name", "")
        origin_id = request.POST.get("origin_id", "")

        with open(full_path, "rb") as f:
            django_file = File(
                f,
                name=full_path.name,
            )
            temp_task = Task(status=TaskStatusEnum.AWAITING)
            django_file.content_type = request.POST.get(
                "mime_type", GENERIC_BINARY_FILE_MIME
            )
            django_file.path = full_path

            processed_file = process_task_file(
                django_file, temp_task, origin_name, origin_id
            )

            with transaction.atomic():
                task = Task.objects.create(
                    status=TaskStatusEnum.AWAITING,
                    uploaded_file=processed_file,
                    source_hash=temp_task.source_hash,
                    mime_type=temp_task.mime_type,
                    media_type=temp_task.media_type,
                )
                AwaitingTaskMetadata.objects.create(
                    task=task,
                    title=request.POST.get("title", ""),
                    description=request.POST.get("description", ""),
                    origin_name=origin_name,
                    origin_id=origin_id,
                    tags=tags,
                )

            return JsonResponse(
                {"task_id": task.id, "status": "success"}, status=201
            )
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid tags data (JSON expected)"}, status=400
        )
    except ValidationError as e:
        return JsonResponse(
            {"error": f"Validation Error: {str(e)}"}, status=400
        )
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def origin_info(request):
    origin_name = request.GET.get("name")
    origin_content_id = request.GET.get("id")
    if not origin_name or not origin_content_id:
        return JsonResponse(
            {
                "status": "error",
                "message": "Missing 'name' or 'id' parameters",
            },
            status=400,
        )

    origin_query = (
        ml_models.ContentOrigin.objects.filter(
            name=origin_name, origin_id=origin_content_id
        )
        .select_related("content")
        .first()
    )
    if origin_query:
        content: ml_models.Content = origin_query.content
        content_url = reverse(
            "content-info", kwargs={"content_slug": content.slug}
        )
        return JsonResponse(
            {
                "status": "found",
                "mlid": content.id,
                "url": content_url,
                "slug": content.slug,
            }
        )
    else:
        return JsonResponse({"status": "not found"}, status=404)


@csrf_exempt
def register_album_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        origin_name = data.get("origin_name")
        album_title = data.get("album_title")
        content_sequence = data.get("content_sequence")
        ordered_content = data.get("ordered_content")

        if not origin_name or not album_title:
            return JsonResponse(
                {"error": "Missing origin_name or album_title"}, status=400
            )

        if content_sequence is not None and ordered_content is not None:
            return JsonResponse(
                {
                    "error": "Provide either content_sequence or ordered_content, not both"
                },
                status=400,
            )

        final_order = {}
        if content_sequence is not None:
            for idx, oid in enumerate(content_sequence):
                final_order[idx + 1] = oid
        elif ordered_content is not None:
            final_order = {int(k): v for k, v in ordered_content.items()}
        else:
            return JsonResponse(
                {"error": "No content data provided"}, status=400
            )

        with transaction.atomic():
            album, created = ml_models.Album.objects.get_or_create(
                album_name=album_title, defaults={"is_nsfw": False}
            )

            if not created:
                ml_models.AlbumOrder.objects.filter(album=album).delete()

            origin_ids = list(final_order.values())
            origins = (
                ml_models.ContentOrigin.objects.filter(
                    name=origin_name, origin_id__in=origin_ids
                )
                .select_related("content")
                .prefetch_related(
                    models.Prefetch(
                        "content__tags",
                        queryset=ml_models.Tag.objects.filter(
                            category=CategoryEnum.CREATOR.value
                        ),
                        to_attr="prefetched_creators",
                    )
                )
            )

            origin_map = {o.origin_id: o.content for o in origins}

            creators_unique = set()
            new_orders = []

            for order_val, oid in final_order.items():
                content_obj = origin_map.get(str(oid))
                if content_obj:
                    for creator in content_obj.prefetched_creators:
                        creators_unique.add(creator)

                    new_orders.append(
                        ml_models.AlbumOrder(
                            album=album, content=content_obj, order=order_val
                        )
                    )

            if new_orders:
                ml_models.AlbumOrder.objects.bulk_create(new_orders)

            if creators_unique:
                album.creator_tags.set(list(creators_unique))

            if not album.album_set:
                tag = ml_models.Tag.objects.filter(
                    title=album_title,
                    category__in=[
                        CategoryEnum.SET.value,
                        CategoryEnum.COMIC.value,
                    ],
                ).first()
                if tag:
                    album.album_set = tag
                    album.save()

        return JsonResponse(
            {
                "status": "success",
                "album_id": album.id,
                "created": created,
                "items_registered": len(new_orders),
                "items_total": len(final_order),
                "creators_found": len(creators_unique),
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
