from medialib.models import Tag, TagAlias, CategoryEnum
from typing import Optional

PREFIXED_CATEGORIES = {
    CategoryEnum.ARTIST,
    CategoryEnum.CHARACTER,
    CategoryEnum.CREATOR,
    CategoryEnum.PROMPTER,
}


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


def resolve_tag(name: str, category: CategoryEnum) -> Tag:
    """
    Находит существующий тег через алиас или название, либо создает новый.
    """
    name = name.lower().strip()

    alias = TagAlias.objects.filter(title=name).select_related("tag").first()
    if alias:
        return alias.tag

    tag, created = Tag.objects.get_or_create(title=name, category=category)

    if created and category in PREFIXED_CATEGORIES:
        prefixed_name = f"{category}:{name}"
        TagAlias.objects.get_or_create(tag=tag, title=prefixed_name)

    return tag


def process_content_tags(content, tags_data: dict[str, list[str]]):
    final_tags_to_add = set()
    processed_ids = set()

    for cat_name, names in tags_data.items():
        try:
            category = CategoryEnum(cat_name)
        except ValueError:
            category = CategoryEnum.CONTENT

        for name in names:
            tag = resolve_tag(name, category)
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
        content.tag_set.add(*final_tags_to_add)
