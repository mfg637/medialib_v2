from ..media_passport import VideoPassport
from base.shared_enums.medialib_model import RepresentationTypeEnum
from image_processing.core.video import ffmpeg
from image_processing.core.encoders import webm, mpeg4_video
from image_processing.core import specification
from . import common
from typing import Optional, Callable
import functools
import logging

vp9_levels = specification.video.LEVELS_VP9
logger = logging.getLogger(__name__)


def safe_media_representation(
    func: Callable[[VideoPassport, int], common.Representation],
):
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Optional[common.Representation]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Failed to create representation in {func.__name__}: {e}"
            )
            return None

    return wrapper


def make_cl1_webm_representation(
    passport: VideoPassport,
) -> common.Representation:
    output_file = passport.source_file.with_stem(
        "{}_cl1".format(passport.source_file.stem)
    ).with_suffix(
        specification.containers.VIDEO_CONTAINDER_FILE_SUFFIX[
            specification.containers.VideoContainers.WEBM
        ]
    )
    webm.encode(
        passport.source_file,
        output_file,
        vp9_levels[1].min_size,
        vp9_levels[1].max_size,
        vp9_levels[1].fps,
        video_bitrate=2000,
        max_video_bitrate=vp9_levels[1].bitrate_limit_kbps,
        copy_audio=False,
        video_level=3.1,
        data=passport.ffprobe_raw_data,
    )
    tmp_passport = VideoPassport(
        output_file,
        specification.containers.VIDEO_CONTAINER_TO_MIME_TYPE[
            specification.containers.VideoContainers.WEBM
        ],
    )
    return common.Representation(
        1,
        output_file,
        tmp_passport.width,
        tmp_passport.height,
        RepresentationTypeEnum.VIDEO,
        tmp_passport.file_format,
        tmp_passport.calc_xxh3_64(),
        tmp_passport.codec_string,
    )


@safe_media_representation
def make_webm_representation(
    passport: VideoPassport, compatibility_level: int
) -> common.Representation:
    output_file = passport.source_file.with_stem(
        "{}_cl{}".format(passport.source_file.stem, compatibility_level)
    ).with_suffix(
        specification.containers.VIDEO_CONTAINDER_FILE_SUFFIX[
            specification.containers.VideoContainers.WEBM
        ]
    )
    is_audio_compatible = False
    if passport.audio_codec is not None:
        is_audio_compatible = (
            passport.audio_codec
            in specification.audio.VIDEO_CONTAINER_COMPATIBLE_CODECS[
                specification.containers.VideoContainers.WEBM
            ]
        )
    webm.encode(
        passport.source_file,
        output_file,
        vp9_levels[compatibility_level].min_size,
        vp9_levels[compatibility_level].max_size,
        vp9_levels[compatibility_level].fps,
        max_video_bitrate=vp9_levels[1].bitrate_limit_kbps,
        copy_audio=is_audio_compatible,
        data=passport.ffprobe_raw_data,
    )
    tmp_passport = VideoPassport(
        output_file,
        specification.containers.VIDEO_CONTAINER_TO_MIME_TYPE[
            specification.containers.VideoContainers.WEBM
        ],
    )
    return common.Representation(
        compatibility_level,
        output_file,
        tmp_passport.width,
        tmp_passport.height,
        RepresentationTypeEnum.VIDEO,
        tmp_passport.file_format,
        tmp_passport.calc_xxh3_64(),
        tmp_passport.codec_string,
    )


def transcode_source_default(
    passport: VideoPassport,
) -> list[common.Representation]:
    representation_list = [make_cl1_webm_representation(passport)]
    if (
        passport.min_size > vp9_levels[1].min_size
        or passport.max_size > vp9_levels[1].max_size
        or passport.fps > vp9_levels[1].fps
    ):
        cl2_representation = make_webm_representation(passport, 2)
        if cl2_representation is not None:
            representation_list.append(cl2_representation)
    if (
        passport.min_size > vp9_levels[2].min_size
        or passport.max_size > vp9_levels[2].max_size
        or passport.fps > vp9_levels[2].fps
    ):
        cl3_representation = make_webm_representation(passport, 3)
        if cl3_representation is not None:
            representation_list.append(cl3_representation)
    return representation_list


def copy_video_mp4(passport: VideoPassport, compatibility_level):
    output_file = passport.source_file.with_stem(
        "{}_out".format(passport.source_file.stem)
    ).with_suffix(
        specification.containers.VIDEO_CONTAINDER_FILE_SUFFIX[
            specification.containers.VideoContainers.MPEG_4
        ]
    )
    ffmpeg.transcoding.mp4_copy_video(passport.source_file, output_file)
    tmp_passport = VideoPassport(
        output_file,
        specification.containers.VIDEO_CONTAINER_TO_MIME_TYPE[
            specification.containers.VideoContainers.MPEG_4
        ],
    )
    return [
        common.Representation(
            compatibility_level,
            output_file,
            tmp_passport.width,
            tmp_passport.height,
            RepresentationTypeEnum.VIDEO,
            tmp_passport.file_format,
            tmp_passport.calc_xxh3_64(),
            tmp_passport.codec_string,
        )
    ]


def transcode_animation_loop(
    passport: VideoPassport, compatibility_level: int
) -> list[common.Representation]:
    mp4_compatible = (
        passport.video_codec is specification.video.VideoCodecs.H264
    )
    if mp4_compatible and compatibility_level <= 1:
        return copy_video_mp4(passport, compatibility_level)
    else:
        output_file = passport.source_file.with_stem(
            "{}_anim".format(passport.source_file.stem)
        ).with_suffix(
            specification.containers.VIDEO_CONTAINDER_FILE_SUFFIX[
                specification.containers.VideoContainers.MPEG_4
            ]
        )
        is_vfr = passport.is_vfr if passport.is_vfr is not None else False
        mpeg4_video.encode(
            passport.source_file,
            output_file,
            is_vfr,
            data=passport.ffprobe_raw_data,
        )
        tmp_passport = VideoPassport(
            output_file,
            specification.containers.VIDEO_CONTAINER_TO_MIME_TYPE[
                specification.containers.VideoContainers.MPEG_4
            ],
        )
        return [
            common.Representation(
                1,
                output_file,
                tmp_passport.width,
                tmp_passport.height,
                RepresentationTypeEnum.VIDEO,
                tmp_passport.file_format,
                tmp_passport.calc_xxh3_64(),
                tmp_passport.codec_string,
            )
        ]


def transcode_mp4_source(
    passport: VideoPassport, compatibility_level: int
) -> list[common.Representation]:
    if passport.audio_codec is not None:
        mp4_compatible = specification.validation.is_mp4_compatible(
            passport.video_codec, passport.audio_codec
        )
    else:
        mp4_compatible = (
            passport.video_codec is specification.video.VideoCodecs.H264
        )
    if mp4_compatible and compatibility_level <= 1:
        return copy_video_mp4(passport, compatibility_level)
    else:
        return transcode_source_default(passport)


def transcode_webm_source(
    passport: VideoPassport, compatibility_level: int
) -> list[common.Representation]:
    representation_list = [make_cl1_webm_representation(passport)]

    representation_from_source = common.Representation(
        compatibility_level,
        passport.source_file,
        passport.width,
        passport.height,
        RepresentationTypeEnum.VIDEO,
        passport.file_format,
        passport.calc_xxh3_64(),
        passport.codec_string,
    )
    if compatibility_level == 2:
        representation_list.append(representation_from_source)
        return representation_list
    elif (
        passport.min_size > vp9_levels[1].min_size
        or passport.max_size > vp9_levels[1].max_size
        or passport.fps > vp9_levels[1].fps
    ):
        cl2_representation = make_webm_representation(passport, 2)
        if cl2_representation is not None:
            representation_list.append(cl2_representation)
    if compatibility_level == 3:
        representation_list.append(representation_from_source)
        return representation_list
    elif (
        passport.min_size > vp9_levels[2].min_size
        or passport.max_size > vp9_levels[2].max_size
        or passport.fps > vp9_levels[2].fps
    ):
        cl3_representation = make_webm_representation(passport, 3)
        if cl3_representation is not None:
            representation_list.append(cl3_representation)
    return representation_list
