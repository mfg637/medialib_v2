from os import getenv
from pathlib import Path
from urllib.parse import quote
from typing import Optional, Callable
import string
from dataclasses import dataclass
from random import choices
from django.db.models import QuerySet
from django.http import (
    HttpRequest,
    HttpResponse,
    Http404,
    FileResponse,
)
from django.db.models import Q
from django.shortcuts import redirect
from medialib_v2.settings import MEDIA_URL
from base.shared_enums.medialib_model import (
    ContentTypeEnum,
    RepresentationTypeEnum,
)
from base.shared_knowledge.file_format import FILE_SUFFIX_TO_FORMAT
from medialib.models import Content, Representation, ContentOrigin

CONTENT_TYPE_TO_REPRESENTATION_TYPE: dict[
    ContentTypeEnum, RepresentationTypeEnum
] = {
    ContentTypeEnum.AUDIO: RepresentationTypeEnum.AUDIO,
    ContentTypeEnum.IMAGE: RepresentationTypeEnum.IMAGE,
    ContentTypeEnum.VIDEO: RepresentationTypeEnum.VIDEO,
    ContentTypeEnum.VIDEO_LOOP: RepresentationTypeEnum.VIDEO,
}


USE_X_ACCEL = bool(int(getenv("USE_X_ACCEL", 0)))


def get_representation(
    content: Content,
    clevel: int,
    content_type: Optional[ContentTypeEnum] = None,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
) -> Optional[Representation]:
    if content_type is None:
        content_type = ContentTypeEnum[content.content_type.upper()]
    reprs = content.representation_set.filter(
        repr_type=CONTENT_TYPE_TO_REPRESENTATION_TYPE[content_type],
        compatibility_level__lte=clevel,
    )
    if not reprs:
        return None
    if content_type is ContentTypeEnum.IMAGE:
        if target_width is None and target_height is None:
            return reprs.order_by("-width", "-compatibility_level").first()
        if target_width is None:
            raise ValueError("width is not set")
        if target_height is None:
            raise ValueError("height is not set")
        large_representations: QuerySet = reprs.filter(
            Q(width__gte=target_width) | Q(height__gte=target_height)
        )
        if large_representations:
            return large_representations.order_by("width").first()
        else:
            return reprs.order_by("-width", "-compatibility_level").first()
    else:
        return reprs.order_by("-compatibility_level").first()


RANDOM_STRING_POPULATION = string.ascii_letters + string.digits


def generate_content_slug_filename(content: Content, suffix: str) -> str:
    return f"{content.slug}{suffix}"


def generate_title_slug_filename(
    content: Content, representation_suffix: str
) -> str:
    safe_title = (
        content.title.replace("/", "_") if content.title else "Untitled"
    )
    valid_origin: Optional[ContentOrigin] = (
        content.origin_set.exclude(origin_id="")
        .filter(alternate=False)
        .first()
    )
    for current_suffix in FILE_SUFFIX_TO_FORMAT:
        if safe_title.endswith(current_suffix):
            safe_title = safe_title.removesuffix(current_suffix)
    if valid_origin:
        origin_info = valid_origin.get_origin_info()
        if origin_info.origin_id is not None:
            return quote(
                f"{origin_info.get_prefix()}{origin_info.origin_id} {safe_title}{representation_suffix}"
            )
    return quote(f"mlid{content.id} {safe_title}{representation_suffix}")


def generate_origin_id_filename(content: Content, suffix: str) -> str:
    valid_origin: ContentOrigin = content.origin_set.exclude(
        origin_id=""
    ).first()
    if valid_origin:
        return f"{valid_origin.origin_id}{suffix}"
    else:
        return f"mlid{content.id}{suffix}"


def generate_random_filename(population: str, suffix: str) -> str:
    random_characters: list[str] = choices(population, k=16)
    random_name = "".join(random_characters)
    return f"{random_name}{suffix}"


def generate_random_string_filename(content: Content, suffix: str) -> str:
    return generate_random_filename(RANDOM_STRING_POPULATION, suffix)


def generate_random_digits_filename(content: Content, suffix: str) -> str:
    return generate_random_filename(string.digits, suffix)


FILE_NAME_FORMATTER: dict[str, Callable[[Content, str], str]] = {
    "content_slug": generate_content_slug_filename,
    "title_slug": generate_title_slug_filename,
    "origin_id": generate_origin_id_filename,
    "random_string": generate_random_string_filename,
    "random_digits": generate_random_digits_filename,
}


@dataclass(frozen=True)
class RepresentationRequestParams:
    content: Content
    clevel: int
    content_type: Optional[ContentTypeEnum]
    target_width: Optional[int]
    target_height: Optional[int]
    filename_format: str = "default"
    download: bool = False


def error_response(error_message) -> HttpResponse:
    r = HttpResponse(f"<h1>400 Invalid Request</h1> {error_message}")
    r.status_code = 400
    return r


def parse_validate_representation_view_params(
    request: HttpRequest, content_slug: str
) -> RepresentationRequestParams | HttpResponse:
    content = Content.objects.get(slug=content_slug)
    content_type_str = request.GET.get("type", "")
    if content_type_str:
        content_type = ContentTypeEnum[content_type_str.upper()]
    else:
        content_type = None
    clevel = request.GET.get("clevel", request.session.get("clevel", 2))
    if clevel:
        clevel = int(clevel)
    else:
        return error_response("clevel can't be None")

    side_size: Optional[int] = (
        int(request.GET["side_size"]) if "side_size" in request.GET else None
    )
    target_width: Optional[int] = (
        int(request.GET["target_width"])
        if "target_width" in request.GET
        else side_size
    )
    target_height: Optional[int] = (
        int(request.GET["target_height"])
        if "target_height" in request.GET
        else side_size
    )
    filename_format = request.GET.get("filename_format", "default")
    if filename_format != "default":
        if filename_format not in FILE_NAME_FORMATTER:
            return error_response("Unknown value of filename_format parmeter")
    download = bool(int(request.GET.get("download", 0)))
    return RepresentationRequestParams(
        content,
        clevel,
        content_type,
        target_width,
        target_height,
        filename_format,
        download,
    )


def get_representation_view(
    request: HttpRequest, content_slug: str
) -> HttpResponse | FileResponse:
    request_params_or_response = parse_validate_representation_view_params(
        request, content_slug
    )
    if isinstance(request_params_or_response, HttpResponse):
        return request_params_or_response

    try:
        representation: Optional[Representation] = get_representation(
            request_params_or_response.content,
            request_params_or_response.clevel,
            request_params_or_response.content_type,
            request_params_or_response.target_width,
            request_params_or_response.target_height,
        )
    except ValueError as e:
        return error_response(e)
    if representation is None:
        raise Http404("Not found any compatible representation")

    abs_file_path = Path(representation.filepath.path)
    if not abs_file_path.exists():
        raise Http404("Physical file not found on disk")

    rel_path = str(representation.filepath)
    if request_params_or_response.filename_format == "default":
        if USE_X_ACCEL:
            response = HttpResponse()
            response["X-Accel-Redirect"] = f"/internal_media/{rel_path}"
            if request_params_or_response.download:
                repr_file_name = abs_file_path.name
                response["Content-Disposition"] = (
                    f'attachment; filename="{repr_file_name}"'
                )
            response["Content-Type"] = representation.get_mime_type()
            return response
        else:
            return redirect(f"/{MEDIA_URL}{rel_path}")

    file_extension = f".{representation.format}"
    new_filename = FILE_NAME_FORMATTER[
        request_params_or_response.filename_format
    ](request_params_or_response.content, file_extension)

    if USE_X_ACCEL:
        response = HttpResponse()
        response["X-Accel-Redirect"] = f"/internal_media/{rel_path}"
        response["Content-Disposition"] = (
            f'attachment; filename="{new_filename}"'
        )
        response["Content-Type"] = representation.get_mime_type()
        return response
    else:
        abs_file_path = Path(representation.filepath.path)
        if not abs_file_path.exists():
            raise Http404("Physical file not found on disk")

        response = FileResponse(
            open(abs_file_path, "rb"),
            content_type=representation.get_mime_type(),
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{new_filename}"'
        )
        return response


def generate_image_srcset(
    content: Content, target_width: int, target_height: int
) -> tuple[str, str]:
    large_representations: QuerySet = content.representation_set.filter(
        repr_type=RepresentationTypeEnum.IMAGE
    ).filter(Q(width__gte=target_width) | Q(height__gte=target_height))
    if large_representations.exists():
        large_representations = large_representations.order_by("width")
        src_list_str: list[str] = []
        for representation in large_representations:
            representation_relation = representation.get_size_relation(
                target_width,
                target_height,
            )
            src_list_str.append(
                (
                    f"/{MEDIA_URL}{quote(str(representation.filepath))} {representation_relation}x"
                )
            )
        base_representation = large_representations.first()
        base_representation_url = (
            f"/{MEDIA_URL}{quote(str(base_representation.filepath))}"
        )
        return ", ".join(src_list_str), base_representation_url
    else:
        largest_representation: Representation = (
            content.representation_set.filter(
                repr_type=RepresentationTypeEnum.IMAGE
            )
            .filter(Q(width__gte=target_width) | Q(height__gte=target_height))
            .order_by("width")
            .last()
        )
        base_representation_url = (
            f"/{MEDIA_URL}{quote(str(largest_representation.filepath))}"
        )
        return "", base_representation_url


def generate_image_srcset_optim_prefetch(
    content: Content, target_width: int, target_height: int
) -> tuple[str, str]:
    def get_relation(repr_w, repr_h, target_w, target_h) -> float:
        if repr_w * target_h >= target_w * repr_h:
            return repr_w / target_w
        else:
            return repr_h / target_h

    all_reprs = content.representation_set.all()

    image_representations = sorted(
        [
            r
            for r in all_reprs
            if r.repr_type == RepresentationTypeEnum.IMAGE.value
        ],
        key=lambda r: r.width,
        reverse=False,
    )

    large_reprs = [
        r
        for r in image_representations
        if r.width >= target_width or r.height >= target_height
    ]

    largest_representation = max(
        image_representations, key=lambda r: r.width * r.height
    )

    if not large_reprs:
        return "", str(largest_representation.filepath)

    src_list_str: list[str] = []
    for representation in large_reprs:
        rel = get_relation(
            representation.width,
            representation.height,
            target_width,
            target_height,
        )
        src_list_str.append(
            f"/{MEDIA_URL}{quote(str(representation.filepath))} {rel}x"
        )

    return ", ".join(src_list_str), str(large_reprs[0].filepath)
