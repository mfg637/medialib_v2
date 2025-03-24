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

def get_image_compatibility_level(size: tuple[int, int], file_format: FormatEnum) -> int:
    level_by_size = get_compatibility_level_by_size(*size)
    level_by_format = FORMAT_LEVEL[file_format]
    return min(level_by_size, level_by_format)