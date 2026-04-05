from urllib.parse import quote, unquote
from typing import Optional
from pathlib import Path
import string
from random import choices
from django.db.models import QuerySet
from django.http import (
    HttpRequest,
    HttpResponse,
    Http404,
    FileResponse,
    HttpResponseRedirect,
)
from typing import Optional
from django.db.models import Q
from django.shortcuts import redirect
from medialib_v2.settings import MEDIA_URL, MEDIALIB_ROOT
from base.shared_enums.medialib_model import (
    ContentTypeEnum,
    RepresentationTypeEnum,
)
from medialib.models import Content, Representation, ContentOrigin


def get_representation(
    request: HttpRequest, content_slug: str
) -> HttpResponse:
    def error_response(param_name) -> HttpResponse:
        r = HttpResponse(
            f"<h1>400 Invalid Request</h1> target {param_name} not set"
        )
        r.status_code = 400
        return r

    content = Content.objects.get(slug=content_slug)
    content_type_str = request.GET.get("type", "")
    if content_type_str:
        content_type = ContentTypeEnum[content_type_str.upper()]
    else:
        content_type = ContentTypeEnum[content.content_type.upper()]
    clevel = request.GET.get("clevel", request.session.get("clevel", 2))
    if clevel:
        clevel = int(clevel)
    else:
        ValueError("clevel can't be None")
    if content_type is ContentTypeEnum.IMAGE:
        side_size: Optional[int] = (
            int(request.GET["side_size"])
            if "side_size" in request.GET
            else None
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
        if target_width is None and target_height is None:
            reprs = content.representation_set.filter(
                repr_type=RepresentationTypeEnum.IMAGE
            ).order_by("-width", "-compatibility_level")
            if reprs.exists():
                for representation in reprs:
                    if representation.compatibility_level <= clevel:
                        return redirect(
                            f"/{MEDIA_URL}{representation.filepath}"
                        )
                raise Http404("Not found any compatible representation")
            raise Http404("Not found any image representation")
        if target_width is None:
            return error_response("width")
        if target_height is None:
            return error_response("height")
        large_representations: QuerySet = content.representation_set.filter(
            repr_type=RepresentationTypeEnum.IMAGE
        ).filter(Q(width__gte=target_width) | Q(height__gte=target_height))
        target_representation: Representation
        if large_representations.exists():
            target_representation = large_representations.order_by(
                "width"
            ).first()
        else:
            target_representation = content.representation_set.order_by(
                "width"
            ).last()
        return redirect(f"/{MEDIA_URL}{target_representation.filepath}")
    elif content_type in {ContentTypeEnum.VIDEO, ContentTypeEnum.VIDEO_LOOP}:
        reprs = content.representation_set.filter(
            repr_type=RepresentationTypeEnum.VIDEO
        ).order_by("-compatibility_level")
        if reprs.exists():
            for representation in reprs:
                if representation.compatibility_level <= clevel:
                    return redirect(f"/{MEDIA_URL}{representation.filepath}")
            raise Http404("Not found any compatible representation")
        raise Http404("Not found any video representation")
    elif content_type is ContentTypeEnum.AUDIO:
        reprs = content.representation_set.filter(
            repr_type=RepresentationTypeEnum.AUDIO
        ).order_by("-compatibility_level")
        if reprs.exists():
            for representation in reprs:
                if representation.compatibility_level <= clevel:
                    return redirect(f"/{MEDIA_URL}{representation.filepath}")
            raise Http404("Not found any compatible representation")
        raise Http404("Not found any audio representation")


RANDOM_STRING_POPULATION = string.ascii_letters + string.digits


def get_representation_with_custom_name(
    request: HttpRequest, content_slug: str
) -> HttpResponse | FileResponse:
    response = get_representation(request, content_slug)

    if not isinstance(response, HttpResponseRedirect):
        return response

    filename_format = request.GET.get("filename_format", "default")
    if filename_format == "default":
        return response

    file_url = response.url

    relative_path_str = file_url.lstrip("/")
    if relative_path_str.startswith(MEDIA_URL.strip("/")):
        relative_path_str = relative_path_str[
            len(MEDIA_URL.strip("/")) :
        ].lstrip("/")

    file_path = Path(unquote(relative_path_str))
    abs_file_path = MEDIALIB_ROOT.joinpath(file_path)
    if not abs_file_path.exists():
        raise Http404("Physical file not found on disk")

    content = Content.objects.get(slug=content_slug)
    representation = content.representation_set.get(
        filepath=str(file_path)
    )  # filepath is unique
    file_extension = f".{representation.format}"

    if filename_format == "title_slug":
        safe_title = (
            content.title.replace("/", "_") if content.title else "Untitled"
        )
        new_filename = f"mlid{content.id} {safe_title}{file_extension}"

    elif filename_format == "origin_id":
        origins = content.origin_set.all()
        valid_origin: Optional[ContentOrigin] = None
        for current_origin in origins:
            if current_origin.origin_id:
                valid_origin = current_origin
                break
        if valid_origin:
            new_filename = f"{valid_origin.origin_id}{file_extension}"
        else:
            new_filename = f"mlid{content.id}{file_extension}"

    elif filename_format == "random_string":
        random_characters: list[str] = choices(RANDOM_STRING_POPULATION, k=16)
        random_name = "".join(random_characters)
        new_filename = f"{random_name}{file_extension}"
    elif filename_format == "random_digits":
        random_characters: list[str] = choices(string.digits, k=16)
        random_name = "".join(random_characters)
        new_filename = f"{random_name}{file_extension}"

    response = FileResponse(
        open(abs_file_path, "rb"),
        content_type=representation.get_mime_type(),
    )
    new_filename = quote(new_filename)

    response["Content-Disposition"] = f'attachment; filename="{new_filename}"'

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
