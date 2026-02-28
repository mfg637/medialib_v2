from typing import Callable
from medialib import models as ml_models
from django.db.models import QuerySet
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
        "safe & !(vector | sketch | simple background | screencap | photo | ai:generated)"
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
