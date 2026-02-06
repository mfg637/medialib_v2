from django.db.models.fields.files import FieldFile
from image_processing.core.file_utils import detect_file_type, MediaType
from base.shared_knowledge.file_format import FormatEnum, MIME_TYPE_TO_FORMAT
from image_processing.core.video.ffmpeg.parser import (
    check_variable_frame_rate_and_estimate_duration,
)
from image_processing.core import specification
from . import media_passport
from pathlib import Path


def create_media_passport(
    source_file: Path, mime_type: str, media_type: MediaType
) -> media_passport.BaseMediaPassport:
    if media_type is MediaType.IMAGE:
        if MIME_TYPE_TO_FORMAT[mime_type] is FormatEnum.GIF:
            vfr_test_data = check_variable_frame_rate_and_estimate_duration(
                source_file
            )
            frames_count = vfr_test_data[2]
            if frames_count > 1:
                return media_passport.VideoPassport(
                    source_file, mime_type, vfr_test_data
                )
            else:
                return media_passport.StaticImagePassport(
                    source_file, mime_type
                )
        else:
            return media_passport.StaticImagePassport(source_file, mime_type)
    elif media_type is MediaType.VIDEO:
        return media_passport.VideoPassport(source_file, mime_type)
    else:
        raise NotImplementedError(f"Unsupported media type: {media_type}")


def detect_compatibility_level(
    passport: media_passport.BaseMediaPassport,
) -> int:
    INCOMPATIBLE_SOURCE_LEVEL = 100
    if isinstance(passport, media_passport.StaticImagePassport):
        return specification.image.get_image_compatibility_level(
            (passport.width, passport.height), passport.file_format
        )

    if isinstance(passport, media_passport.VideoPassport):
        if passport.bit_depth is not None:
            video_cl = specification.validation.calc_video_cl(
                video_codec=passport.video_codec,
                width=passport.width,
                height=passport.height,
                fps=passport.fps,
                bit_depth=passport.bit_depth,
            )
        else:
            return INCOMPATIBLE_SOURCE_LEVEL
        if passport.video_codec == specification.video.VideoCodecs.VP9:
            # CL3 VP9 requires transcoding because of bitrate constraints
            video_cl = max(video_cl, 2)

        audio_cl = 0
        if passport.audio_codec:
            audio_cl = specification.audio.AUDIO_CODEC_LEVEL.get(
                passport.audio_codec, INCOMPATIBLE_SOURCE_LEVEL
            )

        return max(video_cl, audio_cl)

    raise NotImplementedError(f"Unknown passport type: {type(passport)}")


def do_analysis(
    source_file: FieldFile, mime_type: str, media_type_str: str
) -> tuple[media_passport.BaseMediaPassport, int]:
    file_path = Path(source_file.path)
    media_type: MediaType = MediaType(media_type_str)
    passport = create_media_passport(file_path, mime_type, media_type)
    cl = detect_compatibility_level(passport)
    return passport, cl


def analyze_file(
    source_file: Path,
) -> tuple[media_passport.BaseMediaPassport, int]:
    mime_type, media_type = detect_file_type(source_file)
    passport = create_media_passport(source_file, mime_type, media_type)
    cl = detect_compatibility_level(passport)
    return passport, cl
