from base.shared_knowledge.file_format import FormatEnum, MIME_TYPE_TO_FORMAT
from image_processing.core.decoders import video_thumbnail
from .common import Representation
from .image import (
    DefaultRepresentationStrategy,
    JPEG_RepresentationStrategy,
    WEBP_RepresentationStrategy,
    SVG_RepresentationStrategy,
    VideoThumbnailRepresentationStrategy,
)
from .video import (
    transcode_animation_loop,
    transcode_webm_source,
    transcode_mp4_source,
    transcode_source_default,
)
from image_processing.services import media_passport

from typing import Callable
import pathlib

default_strategy = DefaultRepresentationStrategy()
jpeg_strategy = JPEG_RepresentationStrategy()
svg_strategy = SVG_RepresentationStrategy()
webp_strategy = WEBP_RepresentationStrategy()


RepresentationMaker = Callable[[pathlib.Path], list[Representation]]


REPRESENTATION_PROCESSING_STRATEGY: dict[FormatEnum, RepresentationMaker] = {
    FormatEnum.JPEG: jpeg_strategy.make_representations,
    FormatEnum.WEBP: webp_strategy.make_representations,
    FormatEnum.SVG: svg_strategy.make_representations,
}


def get_representation_maker(mime: str) -> RepresentationMaker:
    return REPRESENTATION_PROCESSING_STRATEGY.get(
        MIME_TYPE_TO_FORMAT[mime], default_strategy.make_representations
    )


def make_representations(
    passport: media_passport.BaseMediaPassport, compatibility_level: int
) -> list[Representation]:
    if isinstance(passport, media_passport.StaticImagePassport):
        representations_maker = get_representation_maker(passport.mime)
        return representations_maker(passport.source_file)
    elif isinstance(passport, media_passport.VideoPassport):
        representations = []
        try:
            thumbnail = video_thumbnail.decode(
                passport.source_file, parsed_data=passport.ffprobe_raw_data
            )
        except ValueError as e:
            if passport.mime == "image/gif":
                video_thumbnail_strategy = DefaultRepresentationStrategy()
            else:
                raise e
        else:
            video_thumbnail_strategy = VideoThumbnailRepresentationStrategy(
                thumbnail
            )
        representations.extend(
            video_thumbnail_strategy.make_representations(passport.source_file)
        )
        if passport.content_type == media_passport.ContentTypeEnum.VIDEO_LOOP:
            representations.extend(
                transcode_animation_loop(passport, compatibility_level)
            )
        elif passport.file_format == FormatEnum.WEBM:
            representations.extend(
                transcode_webm_source(passport, compatibility_level)
            )
        elif passport.file_format == FormatEnum.MPEG_4:
            representations.extend(
                transcode_mp4_source(passport, compatibility_level)
            )
        else:
            representations.extend(transcode_source_default(passport))
        return representations
    else:
        raise NotImplementedError(f"Unknown passport format: {type(passport)}")
