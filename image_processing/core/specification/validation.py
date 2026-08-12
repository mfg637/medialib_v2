import logging
from pathlib import Path
from fractions import Fraction
from . import containers, video, audio

logger = logging.getLogger(__name__)


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
            and float(fps) <= spec.fps * 1.0125  # gap to cover tiny overshoot
            and bit_depth <= spec.bit_depth
        ):
            return cl

    return MAX_POSSIBLE_LEVEL


def is_webm_unfinalized(file_path: Path) -> bool:
    SEGMENT_ID = b"\x18\x53\x80\x67"
    logger.debug("is_webm_unfinalized started")

    with open(file_path, "rb") as f:
        header = f.read(4096)

        pos = header.find(SEGMENT_ID)
        if pos == -1:
            logger.debug("segment not found")
            return True

        offset = pos + len(SEGMENT_ID)
        if offset >= len(header):
            logger.debug("invalid size position")
            return True

        first_byte = header[offset]
        if first_byte == 0:
            logger.debug("invalid VINT first byte")
            return True

        vint_len = 1
        mask = 0x80
        while not (first_byte & mask):
            mask >>= 1
            vint_len += 1

        if offset + vint_len > len(header):
            logger.debug("header too short for VINT")
            return True

        vint_bytes = header[offset : offset + vint_len]

        first_byte_data = first_byte & (mask - 1)

        is_unknown_length = (first_byte_data == (mask - 1)) and all(
            b == 0xFF for b in vint_bytes[1:]
        )

        if is_unknown_length:
            logger.debug(
                "Segment length is UNKNOWN (VINT length: %d bytes)", vint_len
            )
            return True

    logger.debug("webm is finalized")
    return False
