from base.shared_enums.medialib_model import CategoryEnum
from base.shared_knowledge.tags import (
    PREFIXED_CATEGORIES,
    prepare_tag_name,
    generate_aliases,
)
from medialib.models import Tag, TagAlias
from typing import Optional


def get_all_implications(
    tag: Tag, visited: Optional[set[int]] = None
) -> set[Tag]:
    if visited is None:
        visited = set()

    if tag.id in visited:
        return set()

    visited.add(tag.id)
    implied_tags = set()

    for implication in tag.implications_target.all():
        child_tag = implication.implicate
        implied_tags.add(child_tag)
        implied_tags.update(get_all_implications(child_tag, visited))

    return implied_tags


def resolve_tag(name: str, category: CategoryEnum) -> tuple[Tag, bool]:
    """
    Finds new tag by (name + category), or alias name, or creates new if not found
    """
    prefixed_aliases: list[str] = []
    PROMPTER_EMBEDED_PREFIX = "prompter:"
    ARTIST_EMBEDED_PREFIX = "artist:"
    name = prepare_tag_name(name)

    if category == CategoryEnum.CONTENT:
        initial_category = category
        if name.startswith(PROMPTER_EMBEDED_PREFIX):
            name = name.removeprefix(PROMPTER_EMBEDED_PREFIX)
            category = CategoryEnum.PROMPTER
        elif name.startswith(ARTIST_EMBEDED_PREFIX):
            name = name.removeprefix(ARTIST_EMBEDED_PREFIX)
            category = CategoryEnum.ARTIST
        if category != initial_category:
            print(
                (
                    "[INCIDENT] Reassigned category "
                    f"'{category}' for tag '{name}' (was '{initial_category}')"
                )
            )

    if category not in PREFIXED_CATEGORIES:
        alias = TagAlias.objects.filter(title=name).first()
        if alias:
            return alias.tag, False
    else:
        prefixed_aliases = generate_aliases(name, category)
        for alias_name in prefixed_aliases:
            alias = TagAlias.objects.filter(title=alias_name).first()
            if alias:
                return alias.tag, False

    tag, created = Tag.objects.get_or_create(title=name, category=category)

    if created:
        aliases: list[str] = prefixed_aliases or generate_aliases(
            name, category
        )
        for aliased_tag in aliases:
            TagAlias.objects.get_or_create(tag=tag, title=aliased_tag)

    return tag, created


def process_content_tags(content, tags_data: dict[str, list[str]]):
    final_tags_to_add = set()
    processed_ids = set()

    for cat_name, names in tags_data.items():
        try:
            category = CategoryEnum(cat_name)
        except ValueError:
            category = CategoryEnum.CONTENT

        for name in names:
            tag, created = resolve_tag(name, category)
            if tag.id not in processed_ids:
                final_tags_to_add.add(tag)
                processed_ids.add(tag.id)

    primary_tags = list(final_tags_to_add)
    for p_tag in primary_tags:
        implications = get_all_implications(p_tag)
        for i_tag in implications:
            if i_tag.id not in processed_ids:
                final_tags_to_add.add(i_tag)
                processed_ids.add(i_tag.id)

    if final_tags_to_add:
        content.tags.add(*final_tags_to_add)
