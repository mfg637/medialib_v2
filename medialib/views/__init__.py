from dataclasses import dataclass
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from base.shared_enums.medialib_model import RepresentationTypeEnum
from medialib_v2.settings import MEDIA_URL
from medialib.models import Content
from medialib.tags.dsl import TagDSLParser, DSLError
from medialib.tags import tag_filter
from . import representation


def content_info(request, content_slug: str) -> HttpResponse:
    content = Content.objects.prefetch_related(
        "representation_set", "origin_set"
    ).get(slug=content_slug)
    all_reprs = content.representation_set.all()
    has_image = any(
        r.repr_type == RepresentationTypeEnum.IMAGE.value for r in all_reprs
    )
    video_representations = sorted(
        [
            r
            for r in all_reprs
            if r.repr_type == RepresentationTypeEnum.VIDEO.value
        ],
        key=lambda r: r.compatibility_level,
        reverse=True,
    )
    srcset_str, base_src = representation.generate_image_srcset_optim_prefetch(
        content, 1024, 1024
    )
    return render(
        request,
        "medialib/content_info.djhtml",
        {
            "content": content,
            "MEDIA_URL": MEDIA_URL,
            "srcset": srcset_str,
            "has_image": has_image,
            "base_src": base_src,
            "video_representations": video_representations,
        },
    )


@dataclass(frozen=True)
class ContentListItem:
    slug: str
    base_src: str
    name: str = ""
    srcset: str = ""


SORTING_ORDER: dict[str, str] = {
    "unsorted": "",
    "date": "addition_date",
    "date decreasing": "-addition_date",
    "random": "?",
}


def content_list(request: HttpRequest) -> HttpResponse:
    query_string = request.GET.get("q", "")
    items_per_page = int(request.GET.get("per_page", 24))
    filter_name = tag_filter.validate_filter(
        request.GET.get("filter", "safe"), request
    )
    sort_mode_name = request.GET.get("sort", "date decreasing")
    if query_string:
        try:
            parser = TagDSLParser(query_string)
            q_object = parser.parse()
            queryset = Content.objects.filter(q_object)
        except DSLError:
            queryset = Content.objects.none()
    else:
        queryset = Content.objects.all()
    filter_function = tag_filter.FILTERS.get(
        filter_name, tag_filter.safety_filter
    )
    queryset = filter_function(queryset).distinct()
    try:
        sorting_order = SORTING_ORDER[sort_mode_name]
    except KeyError:
        sort_mode_name = "date decreasing"
        sorting_order = SORTING_ORDER[sort_mode_name]
    if sorting_order:
        queryset = queryset.order_by(sorting_order)
    queryset = queryset.prefetch_related("representation_set")
    paginator = Paginator(queryset, items_per_page)
    page_number = int(request.GET.get("page", 1))
    page_obj = paginator.get_page(page_number)

    _content_list_raw = page_obj.object_list
    content_list: list[ContentListItem] = []
    for content in _content_list_raw:
        srcset, base_src = representation.generate_image_srcset_optim_prefetch(
            content, 256, 256
        )
        content_list.append(
            ContentListItem(content.slug, base_src, content.title, srcset)
        )
    return render(
        request,
        "medialib/image_grid.djhtml",
        {
            "page_obj": page_obj,
            "content_list": content_list,
            "query_string": query_string,
            "per_page": items_per_page,
            "filter_name": filter_name,
            "available_filters": tag_filter.get_filters_list(request),
            "sorting_mode": sort_mode_name,
            "sorting_modes_available": SORTING_ORDER.keys(),
            "MEDIA_URL": MEDIA_URL,
        },
    )


def set_cl_level(request, level):
    request.session["clevel"] = level
    next_url = request.GET.get("next", "/")
    return redirect(next_url)


__all__ = ["content_info", "content_list", "set_cl_level", "representation"]
