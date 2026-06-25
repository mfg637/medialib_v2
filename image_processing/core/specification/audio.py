import enum
from .containers import AudioContainers, VideoContainers


class AudioCodecs(enum.IntEnum):
    AAC = 0
    Vorbis = 1
    Opus = 2
    UNDEFINED = 999


def codec_name_to_enum(codec_name: str) -> AudioCodecs:
    codec_map = {
        "aac": AudioCodecs.AAC,
        "vorbis": AudioCodecs.Vorbis,
        "opus": AudioCodecs.Opus,
    }
    return codec_map.get(codec_name.lower(), AudioCodecs.UNDEFINED)


AUDIO_CODEC_LEVEL = {
    AudioCodecs.AAC: 0,
    AudioCodecs.Vorbis: 1,
    AudioCodecs.Opus: 1,
}


AUDIO_CODEC_PREFERED_CONTAINER: dict[AudioCodecs, AudioContainers] = {
    AudioCodecs.AAC: AudioContainers.MPEG_4_AUDIO,
    AudioCodecs.Vorbis: AudioContainers.OGG_AUDIO,
    AudioCodecs.Opus: AudioContainers.OGG_OPUS,
}


AUDIO_CODEC_BY_VIDEO_CONTAINER: dict[VideoContainers, AudioCodecs] = {
    VideoContainers.WEBM: AudioCodecs.Opus,
    VideoContainers.MPEG_4: AudioCodecs.AAC,
}


VIDEO_CONTAINER_COMPATIBLE_CODECS: dict[VideoContainers, set[AudioCodecs]] = {
    VideoContainers.MPEG_4: {
        AudioCodecs.AAC,
        AudioCodecs.Opus,
    },
    VideoContainers.WEBM: {
        AudioCodecs.Vorbis,
        AudioCodecs.Opus,
    },
}


def get_aac_codec_str(profile_str: str) -> str:
    profiles = {
        "LC": "2",
        "HE-AAC": "5",
        "HE-AACv2": "29",
    }
    aot = profiles.get(profile_str, "2")
    return f"mp4a.40.{aot}"


def get_opus_codec_str() -> str:
    return "opus"


def get_vorbis_codec_str() -> str:
    return "vorbis"
