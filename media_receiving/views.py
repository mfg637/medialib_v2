import json
import logging
from pathlib import Path
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction, models
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

from base.shared_enums.medialib_model import CategoryEnum
from media_receiving.flow.uploading import process_task_file
from media_receiving.core.file import LocalFile
from medialib import models as ml_models
from .models import Task, AwaitingTaskMetadata, TaskStatusEnum

logger = logging.getLogger(__name__)


class TaskMetadataSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, default="")
    description = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    origin_name = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    origin_id = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    tags = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False,
        default=dict,
    )
    rewrite = serializers.BooleanField(required=False, default=False)


def handle_task_creation(
    file_obj: LocalFile | UploadedFile, metadata, origin_name="", origin_id=""
):
    temp_task = Task(status=TaskStatusEnum.AWAITING)

    processed_file = process_task_file(
        file_obj, temp_task, origin_name, origin_id
    )

    with transaction.atomic():
        task = Task.objects.create(
            status=TaskStatusEnum.AWAITING,
            uploaded_file=processed_file,
            source_hash=temp_task.source_hash,
            mime_type=temp_task.mime_type,
            media_type=temp_task.media_type,
            rewrite=metadata["rewrite"],
        )

        AwaitingTaskMetadata.objects.create(
            task=task,
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            origin_name=origin_name,
            origin_id=str(origin_id),
            tags=metadata.get("tags"),
        )
    return task


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def create_task_api(request):
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response(
            {"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST
        )

    metadata_raw = request.data.get("metadata")
    if metadata_raw and isinstance(metadata_raw, str):
        try:
            data = json.loads(metadata_raw)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON in metadata field"}, status=400
            )
    else:
        data = request.data

    serializer = TaskMetadataSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    clean_data = serializer.validated_data

    try:
        task = handle_task_creation(
            uploaded_file,
            clean_data,
            origin_name=clean_data[  # pyright: ignore[reportIndexIssue, reportOptionalSubscript]
                "origin_name"
            ],
            origin_id=clean_data[  # pyright: ignore[reportIndexIssue, reportOptionalSubscript]
                "origin_id"
            ],
        )

        return Response(
            {
                "task_id": task.id,
                "status": "success",
                "source_hash": (
                    task.source_hash.hex() if task.source_hash else None
                ),
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        logger.exception("API Task creation failed")
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def create_task_from_local_file(request):
    raw_path = request.data.get("file_path", "")
    logger.debug("raw_path: %s", raw_path)
    if not raw_path:
        return Response(
            {"error": "No file_path provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    full_path = Path(raw_path)
    logger.debug("full path '%s'", full_path)
    if not full_path.exists():
        return Response(
            {"error": f"File not found: {full_path}"},
            status=status.HTTP_404_NOT_FOUND,
        )

    data = (
        request.data.copy()
        if hasattr(request.data, "copy")
        else dict(request.data)
    )

    tags_raw = data.get("tags")
    if tags_raw and isinstance(tags_raw, str):
        try:
            data["tags"] = json.loads(tags_raw)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid tags data (JSON expected)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    serializer = TaskMetadataSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    clean_data = serializer.validated_data

    try:
        with open(full_path, "rb") as f:
            django_file = LocalFile(
                f,
                name=full_path.name,
                content_type=request.data.get("mime_type", None),
            )

            task = handle_task_creation(
                django_file,
                clean_data,
                origin_name=clean_data["origin_name"],
                origin_id=clean_data["origin_id"],
            )

            return Response(
                {"task_id": task.id, "status": "success"},
                status=status.HTTP_201_CREATED,
            )

    except ValidationError as e:
        return Response(
            {"error": f"Validation Error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("API Task creation from local file failed")
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class OriginInfoSerializer(serializers.Serializer):
    status = serializers.CharField(default="found")
    mlid = serializers.IntegerField(source="content.id")
    url = serializers.SerializerMethodField()
    slug = serializers.CharField(source="content.slug")

    def get_url(self, obj):
        return reverse(
            "content-info", kwargs={"content_slug": obj.content.slug}
        )


@api_view(["GET"])
def origin_info(request):
    origin_name = request.query_params.get("name")
    origin_content_id = request.query_params.get("id")
    if not origin_name or not origin_content_id:
        return Response(
            {
                "status": "error",
                "message": "Missing 'name' or 'id' parameters",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    origin_query = (
        ml_models.ContentOrigin.objects.filter(
            name=origin_name, origin_id=origin_content_id
        )
        .select_related("content")
        .first()
    )
    if origin_query:
        serializer = OriginInfoSerializer(origin_query)
        return Response(serializer.data)
    else:
        return Response(
            {"status": "not found"}, status=status.HTTP_404_NOT_FOUND
        )


class RegisterAlbumSerializer(serializers.Serializer):
    origin_name = serializers.CharField(required=True)
    album_title = serializers.CharField(required=True)
    content_sequence = serializers.ListField(
        child=serializers.CharField(), required=False, default=None
    )
    ordered_content = serializers.DictField(
        child=serializers.CharField(), required=False, default=None
    )

    def validate(self, data):
        content_seq = data.get("content_sequence")
        ordered_cnt = data.get("ordered_content")

        if content_seq is not None and ordered_cnt is not None:
            raise serializers.ValidationError(
                "Provide either content_sequence or ordered_content, not both"
            )

        if content_seq is None and ordered_cnt is None:
            raise serializers.ValidationError("No content data provided")

        return data


@api_view(["POST"])
def register_album_api(request):
    serializer = RegisterAlbumSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    clean_data = serializer.validated_data

    origin_name = clean_data["origin_name"]
    album_title = clean_data["album_title"]
    content_sequence = clean_data["content_sequence"]
    ordered_content = clean_data["ordered_content"]

    final_order = {}
    if content_sequence is not None:
        for list_index, origin_content_id in enumerate(content_sequence):
            final_order[list_index + 1] = origin_content_id
    else:
        final_order = {int(k): v for k, v in ordered_content.items()}

    try:
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

            for order_val, origin_content_id in final_order.items():
                content_obj = origin_map.get(str(origin_content_id))
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

        return Response(
            {
                "status": "success",
                "album_id": album.id,
                "created": created,
                "items_registered": len(new_orders),
                "items_total": len(final_order),
                "creators_found": len(creators_unique),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.exception("Album registration failed")
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
