from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, Http404
from typing import Optional
from django.db.models import Q
from django.shortcuts import redirect
from medialib_v2.settings import MEDIA_URL
from base.shared_enums.medialib_model import (
    ContentTypeEnum,
    RepresentationTypeEnum,
)
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
    content_type = ContentTypeEnum[request.GET.get("type", "image").upper()]
    clevel = request.session.get("clevel", 2)
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
            ).order_by("-compatibility_level", "-width")
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


def get_relation(repr_w, repr_h, target_w, target_h) -> float:
    if repr_w * target_h >= target_w * repr_h:
        return repr_w / target_w
    else:
        return repr_h / target_h


def generate_image_srcset(
    content: Content, target_width: int, target_height: int
) -> str:
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


def generate_image_srcset_optim_prefetch(
    content: Content, target_width: int, target_height: int
) -> tuple[str, str]:
    all_reprs = content.representation_set.all()

    large_reprs = [
        r
        for r in all_reprs
        if r.width >= target_width or r.height >= target_height
    ]

    largest_representation = max(all_reprs, key=lambda r: r.width * r.height)

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
        src_list_str.append(f"/{MEDIA_URL}{representation.filepath} {rel}x")

    return ", ".join(src_list_str), str(large_reprs[0].filepath)
