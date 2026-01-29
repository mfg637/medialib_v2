import enum
import dataclasses
from .containers import VideoContainers
from typing import Optional


class VideoCodecs(enum.IntEnum):
    H264 = 0
    AVC = H264
    VP8 = 1
    VP9 = 2
    AV1 = 3
    UNDEFINED = 999


def codec_name_to_enum(codec_name: str) -> VideoCodecs:
    codec_map = {
        "h264": VideoCodecs.H264,
        "avc": VideoCodecs.AVC,
        "vp8": VideoCodecs.VP8,
        "vp9": VideoCodecs.VP9,
        "av1": VideoCodecs.AV1,
    }
    return codec_map.get(codec_name.lower(), VideoCodecs.UNDEFINED)


@dataclasses.dataclass(frozen=True)
class LevelDefinition:
    codec: VideoCodecs
    max_size: int
    min_size: int
    fps: int
    bit_depth: int
    bitrate_limit_kbps: int


LEVELS_H264: dict[int, LevelDefinition] = {
    1: LevelDefinition(
        VideoCodecs.H264, 1920, 1080, 60, 8, 60_000
    ),  # approximatelly 4.2
    0: LevelDefinition(
        VideoCodecs.H264, 1920, 1080, 30, 8, 20_000
    ),  # approximatelly 4.1
}

LEVELS_VP9: dict[int, LevelDefinition] = {
    3: LevelDefinition(
        VideoCodecs.VP9, 3840, 2160, 60, 10, 120_000
    ),  # approximatelly 5.1
    2: LevelDefinition(
        VideoCodecs.VP9, 1920, 1080, 60, 8, 60_000
    ),  # approximatelly 4.1
    1: LevelDefinition(
        VideoCodecs.VP9, 1280, 720, 30, 8, 5_000
    ),  # approximatelly 3.1
}

LEVELS_AV1: dict[int, LevelDefinition] = {
    4: LevelDefinition(
        VideoCodecs.AV1, 3840, 2160, 60, 10, 100_000
    ),  # approximatelly 5.1
    3: LevelDefinition(
        VideoCodecs.AV1, 1920, 1080, 60, 10, 40_000
    ),  # approximatelly 4.1
    2: LevelDefinition(
        VideoCodecs.AV1, 1280, 720, 30, 10, 5_000
    ),  # approximatelly 3.1
}

LEVELS_VP8: dict[int, LevelDefinition] = {
    2: LevelDefinition(VideoCodecs.VP8, 1920, 1080, 60, 8, 40_000),
    1: LevelDefinition(VideoCodecs.VP8, 1280, 720, 30, 8, 6_000),
}


PIXEL_FORMAT_TO_BITS_PER_CHANNEL = {"yuv420p": 8, "yuv420p10le": 10}


BITS_PER_CHANNEL_TO_PIXEL_FORMAT = {8: "yuv420p", 10: "yuv420p10le"}


VIDEO_CODEC_PREFERED_CONTAINER: dict[VideoCodecs, VideoContainers] = {
    VideoCodecs.H264: VideoContainers.MPEG_4,
    VideoCodecs.VP8: VideoContainers.WEBM,
    VideoCodecs.VP9: VideoContainers.WEBM,
    VideoCodecs.AV1: VideoContainers.WEBM,
}


CONTAINER_SUPPORTED_VIDEO_CODECS: dict[VideoContainers, set[VideoCodecs]] = {
    VideoContainers.MPEG_4: {
        VideoCodecs.H264,
    },
    VideoContainers.WEBM: {VideoCodecs.VP8, VideoCodecs.VP9, VideoCodecs.AV1},
}


def get_h264_codec_str(
    profile_str: Optional[str], level_idc: Optional[int]
) -> str:
    profiles = {
        "Baseline": 0x42,
        "Main": 0x4D,
        "High": 0x64,
        "High 10": 0x6E,
    }
    if profile_str is None or level_idc is None:
        return "avc1"

    profile_idc = profiles.get(profile_str, profiles["High"])
    return f"avc1.{profile_idc:02x}00{level_idc:02x}".lower()


def get_vp9_codec_str(
    profile_str: Optional[str],
    level_idc: Optional[int],
    bit_depth: Optional[int] = 8,
) -> str:
    import re

    if (
        profile_str is None
        or level_idc is None
        or bit_depth is None
        or level_idc == -99
    ):
        return "vp09"

    profile_match = re.search(r"\d+", profile_str)
    profile_val = profile_match.group(0).zfill(2) if profile_match else "00"

    level_val = str(level_idc).zfill(2)
    bit_depth_val = str(bit_depth).zfill(2)

    return f"vp09.{profile_val}.{level_val}.{bit_depth_val}"


def get_av1_codec_str(
    profile_str: Optional[str],
    level_idc: Optional[int],
    bit_depth: Optional[int] = 8,
) -> str:
    profiles = {"Main": "0", "High": "1", "Professional": "2"}

    if (
        profile_str is None
        or level_idc is None
        or bit_depth is None
        or level_idc == -99
    ):
        return "av01"

    p_val = profiles.get(profile_str, "0")

    l_val = str(level_idc).zfill(2)

    return f"av01.{p_val}.{l_val}M.{bit_depth:02d}"


def get_vp8_codec_str() -> str:
    return "vp8"
