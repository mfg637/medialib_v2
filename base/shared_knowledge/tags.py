from base.shared_enums.medialib_model import CategoryEnum

PREFIXED_CATEGORIES = {
    CategoryEnum.ARTIST,
    CategoryEnum.CHARACTER,
    CategoryEnum.CREATOR,
    CategoryEnum.PROMPTER,
    CategoryEnum.AI,
    CategoryEnum.SET,
}


def prepare_tag_name(name: str) -> str:
    return name.lower().replace("_", " ").strip()


def generate_aliases(tag_name: str, category: CategoryEnum) -> list[str]:
    results = []
    if category in PREFIXED_CATEGORIES:
        prefixed_name = f"{category}: {tag_name}"
    else:
        prefixed_name = tag_name
    results.append(prefixed_name)
    underscored_name = tag_name.replace(" ", "_")
    if category in PREFIXED_CATEGORIES:
        underscored_category = category.value.replace("-", "_")
        underscored_name = f"{underscored_category}:{underscored_name}"
    if underscored_name == prefixed_name:
        return results
    results.append(underscored_name)
    return results
