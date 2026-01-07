import enum
from .containers import AudioContainers, VideoContainers


class AudioCodecs(enum.IntEnum):
    AAC = 0
    Vorbis = 1
    Opus = 2


AUDIO_CODEC_LEVEL = {
    AudioCodecs.AAC: 4,
    AudioCodecs.Vorbis: 3,
    AudioCodecs.Opus: 3,
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
    },
    VideoContainers.WEBM: {
        AudioCodecs.Vorbis,
        AudioCodecs.Opus,
    },
}
