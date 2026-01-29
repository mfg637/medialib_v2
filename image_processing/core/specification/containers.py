import enum
from image_processing.core.file_format import FormatEnum, MIME_TYPE_BY_FORMAT


class VideoContainers(enum.Enum):
    MPEG_4 = enum.auto()
    WEBM = enum.auto()


FFMPEG_VIDEO_CONTAINER_FORMAT = {
    VideoContainers.MPEG_4: "mp4",
    VideoContainers.WEBM: "webm",
}


VIDEO_CONTAINDER_FILE_SUFFIX: dict[VideoContainers, str] = {
    VideoContainers.MPEG_4: ".mp4",
    VideoContainers.WEBM: ".webm",
}


class AudioContainers(enum.Enum):
    MPEG_4_AUDIO = enum.auto()
    OGG_AUDIO = enum.auto()
    OGG_OPUS = enum.auto()


FFMPEG_AUDIO_CONTAINER_FORMAT: dict[AudioContainers, str] = {
    AudioContainers.MPEG_4_AUDIO: "m4a",
    AudioContainers.OGG_AUDIO: "ogg",
    AudioContainers.OGG_OPUS: "opus",
}


AUDIO_CONTAINER_FILE_SUFFIX: dict[AudioContainers, str] = {
    AudioContainers.MPEG_4_AUDIO: ".m4a",
    AudioContainers.OGG_AUDIO: ".oga",
    AudioContainers.OGG_OPUS: ".opus",
}


FILE_FORMAT_TO_CONTAINER_FORMAT: dict[FormatEnum, VideoContainers] = {
    FormatEnum.MPEG_4: VideoContainers.MPEG_4,
    FormatEnum.WEBM: VideoContainers.WEBM,
}

VIDEO_CONTAINER_TO_FILE_FORMAT: dict[VideoContainers, FormatEnum] = {
    VideoContainers.MPEG_4: FormatEnum.MPEG_4,
    VideoContainers.WEBM: FormatEnum.WEBM,
}


VIDEO_CONTAINER_TO_MIME_TYPE: dict[VideoContainers, str] = {
    container: MIME_TYPE_BY_FORMAT[_format]
    for container, _format in VIDEO_CONTAINER_TO_FILE_FORMAT.items()
}
