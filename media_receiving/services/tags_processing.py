from base.shared_enums.medialib_model import CategoryEnum
from medialib.tags.tags_processing import resolve_tag, get_all_implications


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
