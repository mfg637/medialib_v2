from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from typing import Optional
from django.db.models import Q
from django.shortcuts import redirect
from medialib_v2.settings import MEDIA_URL
from base.shared_enums.medialib_model import ContentTypeEnum
from medialib.models import Content, Representation


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
    # currently only IMAGE type supported
    repr_type = ContentTypeEnum[request.GET.get("type", "image").upper()]
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
    if target_width is None and target_height is None:
        return error_response("size")
    if target_width is None:
        return error_response("width")
    if target_height is None:
        return error_response("height")
    large_representations: QuerySet = content.representation_set.filter(
        Q(width__gte=target_width) | Q(height__gte=target_height)
    )
    target_representation: Representation
    if large_representations.exists():
        target_representation = large_representations.order_by("width").first()
    else:
        target_representation = content.representation_set.order_by(
            "width"
        ).last()
    return redirect(f"/{MEDIA_URL}{target_representation.filepath}")


def generate_image_srcset(
    content: Content, target_width: int, target_height: int
) -> str:
    def get_relation(repr_w, repr_h, target_w, target_h) -> float:
        if repr_w * target_h >= target_w * repr_h:
            return repr_w / target_w
        else:
            return repr_h / target_h

    large_representations: QuerySet = content.representation_set.filter(
        Q(width__gte=target_width) | Q(height__gte=target_height)
    )
    if large_representations.exists():
        src_list_str: list[str] = []
        for representation in large_representations:
            representation_relation = get_relation(
                representation.width,
                representation.height,
                target_width,
                target_height,
            )
            src_list_str.append(
                (
                    f"/{MEDIA_URL}{representation.filepath} {representation_relation}x"
                )
            )
        return ", ".join(src_list_str)
    else:
        return ""
