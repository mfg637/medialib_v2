import json
import traceback
from pathlib import Path
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.files import File

from base.shared_knowledge.file_format import GENERIC_BINARY_FILE_MIME
from image_processing.flow.uploading import process_task_file
from medialib import models as ml_models
from .models import Task, AwaitingTaskMetadata, TaskStatusEnum
from .forms import TaskUploadForm


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
    print("raw_path", raw_path)
    if not raw_path:
        return JsonResponse({"error": "No file_path provided"}, status=400)

    full_path = Path(raw_path)

    print(f"full path '{full_path}'")
    if not full_path.exists():
        return JsonResponse(
            {"error": f"File not found: {full_path}"}, status=404
        )

    try:
        tags = json.loads(request.POST.get("tags"))

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

            processed_file = process_task_file(django_file, temp_task)

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
                    origin_name=request.POST.get("origin_name", ""),
                    origin_id=request.POST.get("origin_id", ""),
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
