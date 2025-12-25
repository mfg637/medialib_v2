import enum


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
