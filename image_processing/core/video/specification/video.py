import enum
from .containers import VideoContainers


class VideoCodecs(enum.IntEnum):
    H264 = 0
    AVC = H264
    VP8 = 1
    VP9 = 2
    AV1 = 3


def codec_name_to_enum(codec_name: str) -> VideoCodecs | int:
    codec_map = {
        "h264": VideoCodecs.H264,
        "avc": VideoCodecs.AVC,
        "vp8": VideoCodecs.VP8,
        "vp9": VideoCodecs.VP9,
        "av1": VideoCodecs.AV1,
    }
    return codec_map.get(codec_name.lower(), 999)


LEVELS_60FPS: dict[int, tuple[VideoCodecs, int, int, int]] = {
    1: (VideoCodecs.AV1, 3840, 2160, 10),
    2: (VideoCodecs.VP9, 1920, 1080, 8),
    3: (VideoCodecs.H264, 1920, 1080, 8),
}

LEVELS_30FPS: dict[int, tuple[VideoCodecs, int, int, int]] = {
    1: (VideoCodecs.AV1, 3840, 2160, 10),
    2: (VideoCodecs.VP9, 1920, 1440, 8),
    3: (VideoCodecs.VP9, 1920, 1080, 8),
    4: (VideoCodecs.H264, 1920, 1080, 8),
}


PIXEL_FORMAT_TO_BITS_PER_CHANNEL = {"yuv420p": 8, "yuv420p10le": 10}


BITS_PER_CHANNEL_TO_PIXEL_FORMAT = {8: "yuv420p", 10: "yuv420p10le"}


VIDEO_CODEC_PREFERED_CONTAINER: dict[VideoCodecs, VideoContainers] = {
    VideoCodecs.H264: VideoContainers.MPEG_4,
    VideoCodecs.VP8: VideoContainers.WEBM,
    VideoCodecs.VP9: VideoContainers.WEBM,
    VideoCodecs.AV1: VideoContainers.WEBM,
}
