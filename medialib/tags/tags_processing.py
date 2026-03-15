from base.shared_enums.medialib_model import CategoryEnum
from base.shared_knowledge.tags import (
    PREFIXED_CATEGORIES,
    prepare_tag_name,
    generate_aliases,
)
from medialib.models import Tag, TagAlias, TagImplications
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

    def post_process(tag: Tag, created: bool) -> tuple[Tag, bool]:
        if tag.category in {CategoryEnum.ARTIST, CategoryEnum.PROMPTER}:
            implied_tag, implied_created = resolve_tag(
                tag.title, CategoryEnum.CREATOR
            )
            TagImplications.objects.get_or_create(
                target=tag, implicate=implied_tag
            )
            return tag, created or implied_created
        else:
            return tag, created

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
            aliased_tag = alias.tag
            if (
                category != CategoryEnum.CONTENT
                and aliased_tag.category == CategoryEnum.CONTENT
            ):
                print(
                    "[INCIDENT] Reassigned category "
                    f"'{category}' for tag '{name}' (was 'content')"
                )
                aliased_tag.category = category
                aliased_tag.save()
            return post_process(alias.tag, False)
    else:
        prefixed_aliases = generate_aliases(name, category)
        for alias_name in prefixed_aliases:
            alias = TagAlias.objects.filter(title=alias_name).first()
            if alias:
                return post_process(alias.tag, False)

    tag, created = Tag.objects.get_or_create(title=name, category=category)

    if created:
        aliases: list[str] = prefixed_aliases or generate_aliases(
            name, category
        )
        for aliased_tag in aliases:
            TagAlias.objects.get_or_create(tag=tag, title=aliased_tag)

    return post_process(tag, created)
