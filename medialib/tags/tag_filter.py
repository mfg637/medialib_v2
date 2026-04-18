from typing import Callable
from medialib import models as ml_models
from django.db.models import QuerySet
from django.http import HttpRequest
from .dsl import TagDSLParser


def bypass(
    queryset: QuerySet[ml_models.Content],
) -> QuerySet[ml_models.Content]:
    return queryset


def basic_filter(
    queryset: QuerySet[ml_models.Content],
) -> QuerySet[ml_models.Content]:
    """
    Hides only manually hidden content
    """
    return queryset.filter(is_hidden=False)


def safety_filter(
    queryset: QuerySet[ml_models.Content],
) -> QuerySet[ml_models.Content]:
    q_object = TagDSLParser("safe").parse()
    return basic_filter(queryset).filter(q_object)


def aesthetic_filter(
    queryset: QuerySet[ml_models.Content],
) -> QuerySet[ml_models.Content]:
    q_object = TagDSLParser(
        "safe & !(vector | sketch | simple background | screencap | photo | ai:generated | comic)"
    ).parse()
    return basic_filter(queryset).filter(q_object)


FILTERS: dict[
    str,
    Callable[
        [
            QuerySet,
        ],
        QuerySet[ml_models.Content],
    ],
] = {
    "bypass": bypass,
    "basic": basic_filter,
    "safe": safety_filter,
    "aesthetic": aesthetic_filter,
}

UNAUTHENTICATED_FILTERS = {"safe", "aesthetic"}


def get_filters_list(is_nsfw_member: bool):
    if is_nsfw_member:
        return FILTERS.keys()
    else:
        return list(UNAUTHENTICATED_FILTERS)


def validate_filter(filter_name: str, is_nsfw_member: bool):
    if is_nsfw_member:
        if filter_name in FILTERS:
            return filter_name
    else:
        if filter_name in UNAUTHENTICATED_FILTERS:
            return filter_name
    return "safe"
