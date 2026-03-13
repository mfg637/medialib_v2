from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from medialib.models import Tag
from . import representation, content, collection, album


def set_cl_level(request: HttpRequest, level: int) -> HttpResponse:
    request.session["clevel"] = level
    next_url = request.GET.get("next", "/")
    return redirect(next_url)


def tag_info(request: HttpRequest, tag_id: int) -> HttpResponse:
    tag = get_object_or_404(Tag, id=tag_id)
    context = {
        "tag": tag,
        "aliases": tag.alias_set.all(),
        "implications": tag.implications.all(),
        "is_implied_by": tag.is_implied_by.all(),
    }
    return render(request, "medialib/tag_info.djhtml", context)


__all__ = [
    "content",
    "set_cl_level",
    "representation",
    "tag_info",
    "collection",
    "album",
]
