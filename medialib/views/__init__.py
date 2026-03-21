from django.db.models import QuerySet
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from medialib.models import Tag, TagAlias
from . import representation, content, collection, album
from typing import Optional


def set_cl_level(request: HttpRequest, level: int) -> HttpResponse:
    request.session["clevel"] = level
    next_url = request.GET.get("next", "/")
    return redirect(next_url)


def get_valid_alias_query(alias_set: QuerySet[TagAlias]) -> Optional[TagAlias]:
    BANNED_CHARACTERS = set(
        "(){}[]!&|"
    )  # these characters reserved by DSL syntax

    for alias in alias_set:
        if not (set(alias.title) & BANNED_CHARACTERS):
            return alias
    return None


def tag_info(request: HttpRequest, tag_id: int) -> HttpResponse:
    tag = get_object_or_404(Tag, id=tag_id)
    alias_set = tag.alias_set.all()
    valid_alias = get_valid_alias_query(alias_set)
    context = {
        "tag": tag,
        "aliases": alias_set,
        "implications": tag.implications.all(),
        "is_implied_by": tag.is_implied_by.all(),
        "valid_alias": valid_alias,
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
