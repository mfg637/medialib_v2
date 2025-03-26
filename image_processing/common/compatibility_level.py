import enum
from .file_format import FormatEnum

cl3_video_width = 1280
cl3_video_height = 720


CL3_FFMPEG_SCALE_COMMANDLINE = [
    '-vf', 'scale=\'min({},iw)\':\'min({},ih)\':force_original_aspect_ratio=decrease'.format(
        cl3_video_width, cl3_video_height
    )
]

def cl3_size_valid(video):
    return video["width"] <= cl3_video_width and video["height"] <= cl3_video_height


IMAGE_SIZE_LIMIT = {
    0: None,
    1: 2 ** 13,
    2: 2 ** 12,
    3: 2 ** 11,
    4: 2 ** 10
}

def get_compatibility_level_by_size(width: int, height: int) -> int:
    max_size = max(width, height)
    for i in range(4, 0, -1):
        if max_size <= IMAGE_SIZE_LIMIT[i]:
            return i
    return 0

FORMAT_LEVEL: dict[FormatEnum, int] = {
    FormatEnum.PNG: 4,
    FormatEnum.JPEG: 4,
    FormatEnum.GIF: 4,
    FormatEnum.MPEG_4: 4,
    FormatEnum.WEBP: 3,
    FormatEnum.WEBM: 3,
    FormatEnum.AVIF: 2,
    FormatEnum.SVG: 0
}

ENCODING_FORMAT_BY_LEVEL: dict[int, FormatEnum] = {
    0: FormatEnum.AVIF,
    1: FormatEnum.AVIF,
    2: FormatEnum.AVIF,
    3: FormatEnum.WEBP,
    4: FormatEnum.JPEG
}

def get_image_compatibility_level(size: tuple[int, int], file_format: FormatEnum) -> int:
    level_by_size = get_compatibility_level_by_size(*size)
    level_by_format = FORMAT_LEVEL[file_format]
    return min(level_by_size, level_by_format)

def calc_representations_format(size: tuple[int, int], file_format: FormatEnum)\
        -> dict[int, tuple[FormatEnum, int, int] | None]:
    result = {
        0: None,
        1: None,
        2: None,
        3: None,
        4: None
    }
    level_by_size = get_compatibility_level_by_size(*size)
    level_by_format = FORMAT_LEVEL[file_format]
    current_level = 0
    current_size = size
    size_divider = 2
    if level_by_format < level_by_size:
        result[level_by_format] = (file_format, size[0], size[1])
        result[level_by_size] = (ENCODING_FORMAT_BY_LEVEL[level_by_size], size[0], size[1])
        current_level = level_by_size
    else:
        current_format = file_format
        if file_format == FormatEnum.PNG:
            current_format = ENCODING_FORMAT_BY_LEVEL[level_by_size]
        current_level = level_by_size
        result[current_level] = (current_format, size[0], size[1])
    while current_level < 4:
        current_level += 1
        while get_compatibility_level_by_size(*current_size) < current_level:
            current_size = (round(size[0] / size_divider), round(size[1] / size_divider))
            size_divider *= 2
        result[current_level] = (
            ENCODING_FORMAT_BY_LEVEL[current_level], current_size[0], current_size[1]
        )
    return result


class VideoCodecs(enum.StrEnum):
    H264 = "H264"
    AVC = H264
    VP8 = "VP8"
    VP9 = "VP9"
    AV1 = "AV1"


class AudioCodecs(enum.StrEnum):
    MPEG_L3 = "MP3"
    AAC = "AAC"
    Vorbis = "Vorbis"
    Opus = "Opus"
    FLAC = "FLAC"


# CL: (Codec, width, height, bits per channel)
VIDEO_60FPS_LEVELS: dict[int, tuple[VideoCodecs, int, int, int]] = {
    1: (VideoCodecs.AV1, 3840, 2160, 10),
    2: (VideoCodecs.VP9, 2560, 1440, 8),
    3: (VideoCodecs.H264, 1920, 1080, 8),
}

VIDEO_30FPS_LEVELS: dict[int, tuple[VideoCodecs, int, int, int]] = {
    1: (VideoCodecs.AV1, 7680, 4320, 10),
    2: (VideoCodecs.VP9, 3840, 2160, 8),
    3: (VideoCodecs.VP9, 1920, 1080, 8),
    4: (VideoCodecs.H264, 1920, 1080, 8),
}