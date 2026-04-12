from dataclasses import dataclass
from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from base.shared_enums.medialib_model import (
    ContentTypeEnum,
    RepresentationTypeEnum,
)
from medialib_v2.settings import MEDIA_URL
from medialib.models import Content, ImageHash, Collection, ContentRedirect
from medialib.tags.dsl import TagDSLParser, DSLError
from medialib.tags import tag_filter
from . import representation


@dataclass(frozen=True)
class ContentListItem:
    id: int
    slug: str
    base_src: str
    content_type: str
    name: str = ""
    srcset: str = ""


def get_similar_content(content, limit=50):
    try:
        current_hash = ImageHash.objects.get(content=content)
    except ImageHash.DoesNotExist:
        return None

    similar_hash = current_hash.far_similarity

    similar_hashes = (
        ImageHash.objects.filter(far_similarity=similar_hash)
        .exclude(content=content)
        .select_related("content")[:limit]
    )

    similar_items = []
    for h in similar_hashes:
        srcset, base_src = representation.generate_image_srcset_optim_prefetch(
            h.content, 128, 128
        )
        similar_items.append(
            ContentListItem(
                h.content.id,
                h.content.slug,
                base_src,
                h.content.content_type,
                h.content.title,
                srcset,
            )
        )
    return similar_items


def _content_info(request: HttpRequest, content: Content) -> HttpResponse:
    all_tags = content.tags.all()
    user_collections = Collection.objects.none()
    if request.user.is_authenticated:
        user_collections = (
            Collection.objects.filter(user=request.user)
            .exclude(items=content)
            .order_by("title")
        )
    else:
        is_safe = any(t.title == "safe" for t in all_tags)
        if not is_safe:
            raise PermissionDenied("This content is unavailable.")
    grouped_tags: dict[str, list[tuple[int, str]]] = {}
    for tag in all_tags:
        if tag.category not in grouped_tags:
            grouped_tags[tag.category] = []
        grouped_tags[tag.category].append((tag.id, tag.title))
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
    similar_content = None
    if (
        content.get_content_type() is ContentTypeEnum.IMAGE
        and request.user.is_authenticated
    ):
        similar_content = get_similar_content(content)
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
            "grouped_tags": grouped_tags,
            "similar_content": similar_content,
            "user_collections": user_collections,
        },
    )


def content_info_by_slug(request, content_slug: str) -> HttpResponse:
    try:
        content = Content.objects.prefetch_related(
            "representation_set",
            "origin_set",
            "tags",
            "album_item",
            "album_item__album",
        ).get(slug=content_slug)
        return _content_info(request, content)

    except Content.DoesNotExist:
        redirect_obj = (
            ContentRedirect.objects.select_related("new_content")
            .filter(old_slug=content_slug)
            .first()
        )

        if redirect_obj:
            return redirect(
                "content-info",
                content_slug=redirect_obj.new_content.slug,
                permanent=True,
            )

        raise Http404(_("Content not found"))


def content_info_by_id(request, content_id: int) -> HttpResponse:
    content = Content.objects.prefetch_related(
        "representation_set",
        "origin_set",
        "tags",
        "album_item",
        "album_item__album",
    ).get(id=content_id)
    return _content_info(request, content)


SORTING_ORDER: dict[str, str] = {
    "unsorted": "",
    "date": "addition_date",
    "date decreasing": "-addition_date",
    "random": "?",
}


def get_items_per_page(request: HttpRequest) -> int:
    session_per_page = int(request.session.get("per_page", 24))
    try:
        items_per_page = int(request.GET.get("per_page", session_per_page))
    except ValueError:
        items_per_page = 24
    items_per_page = max(min(items_per_page, 1000), 3)
    if items_per_page != session_per_page:
        request.session["per_page"] = items_per_page
    return items_per_page


def content_list(request: HttpRequest) -> HttpResponse:
    query_string = request.GET.get("q", "")
    items_per_page = get_items_per_page(request)
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
            ContentListItem(
                content.id,
                content.slug,
                base_src,
                content.content_type,
                content.title,
                srcset,
            )
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


__all__ = ["content_info", "content_list"]
