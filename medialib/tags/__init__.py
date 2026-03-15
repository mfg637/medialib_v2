from django.db.models import Case, When, Value, IntegerField, Q, QuerySet
from base.shared_knowledge.tags import prepare_tag_name
from medialib.models import Tag
from typing import Optional
from . import dsl, tag_filter, tags_processing


def smart_tag_search(
    search_term: str, queryset: Optional[QuerySet[Tag]] = None
):
    search_term = prepare_tag_name(search_term)
    if queryset is None:
        queryset = Tag.objects.all()
    # note: tags already processed with prepare_tag_name().
    # case insensitive search not required

    return (
        queryset.filter(
            Q(title__contains=search_term)
            | Q(alias_set__title__contains=search_term)
        )
        .annotate(
            relevance=Case(
                When(title=search_term, then=Value(1)),
                When(alias_set__title=search_term, then=Value(2)),
                When(alias_set__title__contains=search_term, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        )
        .order_by("relevance", "title")
        .distinct()
    )


__all__ = ["smart_tag_search", "dsl", "tag_filter", "tags_processing"]
