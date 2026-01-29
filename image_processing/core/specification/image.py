from image_processing.core.file_format import FormatEnum

IMAGE_SIZE_LIMIT = {4: None, 3: 2**13, 2: 2**12, 1: 2**11, 0: 2**10}


FORMAT_LEVEL: dict[FormatEnum, int] = {
    FormatEnum.PNG: 0,
    FormatEnum.JPEG: 0,
    FormatEnum.GIF: 0,
    FormatEnum.MPEG_4: 0,
    FormatEnum.WEBP: 1,
    FormatEnum.WEBM: 1,
    FormatEnum.AVIF: 2,
    FormatEnum.SVG: 3,
}

ENCODING_FORMAT_BY_LEVEL: dict[int, FormatEnum] = {
    4: FormatEnum.AVIF,
    3: FormatEnum.AVIF,
    2: FormatEnum.AVIF,
    1: FormatEnum.WEBP,
    0: FormatEnum.JPEG,
}


def get_compatibility_level_by_size(width: int, height: int) -> int:
    max_dim = max(width, height)
    for cl in range(0, 4):
        limit = IMAGE_SIZE_LIMIT[cl]
        if max_dim <= limit:
            return cl
    return 4


def get_image_compatibility_level(
    size: tuple[int, int], file_format: FormatEnum
) -> int:
    level_by_size = get_compatibility_level_by_size(*size)
    level_by_format = FORMAT_LEVEL.get(file_format, 0)
    return max(level_by_size, level_by_format)
