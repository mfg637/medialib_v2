from fractions import Fraction
from . import containers, video, audio


def is_container_compatible(
    container: containers.VideoContainers,
    video_codec: video.VideoCodecs,
    audio_codec: audio.AudioCodecs,
) -> bool:
    is_video_compatible = (
        video_codec in video.CONTAINER_SUPPORTED_VIDEO_CODECS[container]
    )
    is_audio_compatible = (
        audio_codec in audio.VIDEO_CONTAINER_COMPATIBLE_CODECS[container]
    )
    return is_video_compatible and is_audio_compatible


def is_mp4_compatible(
    video_codec: video.VideoCodecs, audio_codec: audio.AudioCodecs
) -> bool:
    return is_container_compatible(
        containers.VideoContainers.MPEG_4, video_codec, audio_codec
    )


def is_webm_compatible(
    video_codec: video.VideoCodecs, audio_codec: audio.AudioCodecs
) -> bool:
    return is_container_compatible(
        containers.VideoContainers.WEBM, video_codec, audio_codec
    )


def test_video_cl(
    compatibility_level: int,
    video_codec: video.VideoCodecs,
    min_size: int,
    max_size: int,
    fps: Fraction | float | int,
    bit_depth: int,
) -> bool:
    fps60_level = video.LEVELS_60FPS[compatibility_level]
    fps30_level = video.LEVELS_30FPS[compatibility_level]
    if fps > 30 * 1.0125:
        return (
            fps <= 60
            and video_codec.value <= fps60_level[0].value
            and max_size <= fps60_level[1]
            and min_size <= fps60_level[2]
            and bit_depth <= fps60_level[3]
        )
    else:
        return (
            video_codec <= fps30_level[0].value
            and max_size <= fps30_level[1]
            and min_size <= fps30_level[2]
            and bit_depth <= fps30_level[3]
        )


def calc_video_cl(
    video_codec: video.VideoCodecs,
    width: int,
    height: int,
    fps: Fraction | float | int,
    bit_depth: int,
) -> int:
    """
    Calculates minimal CL, suitable for current video prameters.
    Returns MAX_POSSIBLE_LEVEL, if codec unknown.
    """
    MAX_POSSIBLE_LEVEL = 4
    codec_levels_map = {
        video.VideoCodecs.H264: video.LEVELS_H264,
        video.VideoCodecs.VP8: video.LEVELS_VP8,
        video.VideoCodecs.VP9: video.LEVELS_VP9,
        video.VideoCodecs.AV1: video.LEVELS_AV1,
    }

    levels = codec_levels_map.get(video_codec)

    if not levels:
        return MAX_POSSIBLE_LEVEL

    sorted_cl_indices = sorted(levels.keys())

    max_dim = max(width, height)
    min_dim = min(width, height)

    for cl in sorted_cl_indices:
        spec = levels[cl]

        if (
            max_dim <= spec.max_size
            and min_dim <= spec.max_size
            and float(fps) <= spec.fps * 1.0125
            and bit_depth <= spec.bit_depth
        ):
            return cl

    return MAX_POSSIBLE_LEVEL
