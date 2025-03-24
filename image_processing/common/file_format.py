import enum


class FormatEnum(enum.StrEnum):
    PNG = "PNG"
    JPEG = "JPEG"
    GIF = "GIF"
    MPEG_4 = "MPEG 4"
    WEBP = "WEBP"
    WEBM = "WEBM"
    AVIF = "AVIF"
    SVG = "SVG"


FILE_SUFFIX_TO_FORMAT: dict[str, FormatEnum] = {
    ".png": FormatEnum.PNG,
    ".jpg": FormatEnum.JPEG,
    ".jpeg": FormatEnum.JPEG,
    ".jfif": FormatEnum.JPEG,
    ".gif": FormatEnum.GIF,
    ".mp4": FormatEnum.MPEG_4,
    ".m4v": FormatEnum.MPEG_4,
    ".webp": FormatEnum.WEBP,
    ".webm": FormatEnum.WEBM,
    ".avif": FormatEnum.AVIF,
    ".svg": FormatEnum.SVG
}

MIME_TYPE_TO_FORMAT: dict[str, FormatEnum] = {
    "image/png": FormatEnum.PNG,
    "image/jpeg": FormatEnum.JPEG,
    "image/gif": FormatEnum.GIF,
    "video/mp4": FormatEnum.MPEG_4,
    "image/webp": FormatEnum.WEBP,
    "video/webm": FormatEnum.WEBM,
    "image/avif": FormatEnum.AVIF,
    "image/svg+xml": FormatEnum.SVG,
}