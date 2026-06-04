import enum
from fractions import Fraction
import json
from typing import Optional, Any


from image_processing.core.utils import (
    run_subprocess,
    InputSourceFacade,
    SourceType,
    check_is_fractions,
    to_fractions_or_float,
)


def fps_calc(raw_str) -> Fraction | int | float:
    """
    Convert ffprobe's string representation of FPS to number
    """
    _f = raw_str.split("/")
    if len(_f) == 1:
        return int(_f[0])
    elif len(_f) == 2:
        _f = (int(_f[0]), int(_f[1]))
        if check_is_fractions(_f):
            return to_fractions_or_float(_f)
        elif _f[1] == 0:
            raise ValueError("Not defined")
        else:
            raise ValueError(f"Unexpected fps value format: {raw_str}")
    else:
        raise ValueError(f"Unexpected fps value format: {raw_str}")


def get_fps(video_stream):
    """
    Get FPS information from video stream data
    """
    fps = None
    if video_stream["avg_frame_rate"] == "0/0":
        fps = fps_calc(video_stream["r_frame_rate"])
    else:
        fps = fps_calc(video_stream["avg_frame_rate"])
    return fps


def get_duration(data):
    return float(data["format"]["duration"])


class SPECIFY_VIDEO_STREAM(enum.Enum):
    FIRST = enum.auto()
    LAST = enum.auto()


def get_video_streams(data) -> list[dict]:
    video_streams = []
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            video_streams.append(stream)
    return video_streams


def find_video_stream(
    data, first_or_last=SPECIFY_VIDEO_STREAM.FIRST
) -> Optional[dict]:
    video = None
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            video = stream
            if first_or_last == SPECIFY_VIDEO_STREAM.FIRST:
                break
    return video


def find_audio_streams(data) -> list[dict]:
    streams = list()
    for stream in data["streams"]:
        if stream["codec_type"] == "audio":
            streams.append(stream)
    return streams


def get_file_bitrate(data):
    return int(data["format"]["bit_rate"])


def get_video_codec(video_stream) -> str:
    return video_stream["codec_name"]


def get_video_pixel_format(video_stream) -> str:
    return video_stream["pix_fmt"]


def check_variable_frame_rate_and_estimate_duration(
    source: SourceType,
) -> tuple[float, bool, int]:
    """
    Returns: estimated duration, is VFR, frames count
    """
    with InputSourceFacade(source) as source_handler:
        file_path = source_handler.get_file_str()
        commandline = [
            "ffprobe",
            "-show_entries",
            "frame=duration_time",
            "-print_format",
            "json",
            file_path,
        ]
        result = run_subprocess(commandline)
    raw_data = result.stdout.decode()
    json_data = json.loads(raw_data)
    first_value = None
    duration_sum = 0.0
    vfr = False
    for frame in json_data["frames"]:
        duration_time_raw = frame["duration_time"]
        if first_value is None:
            first_value = duration_time_raw
        else:
            if duration_time_raw != first_value:
                vfr = True
        duration_time = float(duration_time_raw)
        duration_sum += duration_time
    return duration_sum, vfr, len(json_data["frames"])


def test_videoloop(
    src_metadata, estimated_duration: Optional[float] = None
) -> bool:
    audio_streams = find_audio_streams(src_metadata)
    if len(audio_streams) > 0:
        return False
    else:
        try:
            duration = get_duration(src_metadata)
        except KeyError:
            duration = estimated_duration
        if duration is None:
            raise ValueError("Invalid duration")
        if duration <= 30.0:
            return True
        else:
            return False


def get_video_size(video_stream) -> tuple[int, int, int, int]:
    """
    Get size of video stream
    Returns: width, height, minimum size, maximum size
    """
    width = video_stream["width"]
    height = video_stream["height"]
    if width > height:
        min_size = height
        max_size = width
    else:
        min_size = width
        max_size = height
    return width, height, min_size, max_size


def test_video_cl3(src_metadata) -> bool:
    video = find_video_stream(src_metadata)
    if video is None:
        raise ValueError("not found video in media file")
    fps = get_fps(video)
    if video["pix_fmt"] != "yuv420p":
        return False
    width, height, min_size, max_size = get_video_size(video)
    if video["codec_name"] in ("vp9", "vp8"):
        if min_size <= 720 and max_size <= 1280 and fps <= 60:
            return True
        elif min_size <= 1080 and max_size <= 1920 and fps <= 30:
            return True
    elif video["codec_name"] == "h264":
        return min_size <= 1080 and max_size <= 1920 and fps <= 60
    return False


def get_size(src_metadata) -> tuple[int, int]:
    """
    Shorter version of get_video_size(), that reads size from `data` dict
    Returns: width, height
    """
    video = find_video_stream(src_metadata)
    if video is None:
        raise ValueError("not found video in media file")
    return video["width"], video["height"]


def fps(src_metadata):
    """
    Get FPS info from first video stream from general data object
    """
    video = find_video_stream(src_metadata)
    return get_fps(video)


def has_alpha_channel(pix_fmt: str) -> bool:
    """
    Determines presense of alpha channel by pixel format string value.
    """
    if not pix_fmt:
        return False

    hardware_or_special = {"vaapi", "cuda", "dxva2", "vulkan", "bayer", "qsv"}
    if any(spec in pix_fmt for spec in hardware_or_special):
        return False

    alpha_indicators = [
        "rgba",
        "bgra",
        "argb",
        "abgr",
        "yuva",
        "ya8",
        "ya16",
        "gbrap",
        "ayuv",
    ]

    if any(indicator in pix_fmt for indicator in alpha_indicators):
        return True

    return False


def get_codec_name(stream_data) -> str:
    return stream_data["codec_name"]


def get_profile_and_level_if_exists(
    video_stream: dict[str, Any],
) -> tuple[Optional[str], Optional[int]]:
    profile = video_stream.get("profile", None)
    if profile is not None:
        profile = str(profile)
    level = video_stream.get("level", None)
    if level is not None:
        level = int(level)
    return profile, level
