from base.shared_enums.medialib_model import RepresentationTypeEnum

REPRESENATION_FILE_PATH_LIMIT = 512
TAG_NAME_LENGTH_LIMIT = 512
TAG_ALIAS_LENGRG_LIMIT = TAG_NAME_LENGTH_LIMIT
SOURCE_HASH_BINARY_LENGTH = 32
YEAR_DIGITS = 4
MONTH_DAY_DIGITS = 2
SOURCE_HASH_HEX_LENGTH = SOURCE_HASH_BINARY_LENGTH * 2
HYPHEN_COUNT = 3
SLUG_LENGTH = (
    YEAR_DIGITS + MONTH_DAY_DIGITS * 2 + SOURCE_HASH_HEX_LENGTH + HYPHEN_COUNT
)


COMPATIBILITY_LEVEL_MAPPING = [
    (4, "CL4 Supercomputer"),
    (3, "CL3 Personal Computer"),
    (2, "CL2 Mobile device"),
    (1, "CL1 Old hardware"),
    (0, "CL0 Very old hardware"),
]
COMPATIBILITY_LEVEL_DICT: dict[int, str] = {
    CL[0]: CL[1] for CL in COMPATIBILITY_LEVEL_MAPPING
}
REPRESENTATION_TYPE_MAPPING = [
    (RepresentationTypeEnum.IMAGE.value, "Image"),
    (RepresentationTypeEnum.VIDEO.value, "Video"),
    (RepresentationTypeEnum.AUDIO.value, "Audio"),
]
REPRESENTATION_TYPE_DICT: dict[int, str] = {
    repr_type[0]: repr_type[1] for repr_type in REPRESENTATION_TYPE_MAPPING
}
