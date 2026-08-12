from typing import Optional
from pathlib import Path
from base.shared_enums.medialib_model import ContentTypeEnum
from base.shared_knowledge.file_format import MIME_TYPE_TO_FORMAT, FormatEnum
from image_processing.core.file_utils import calc_sha256, calc_xxh3_64
from image_processing.core.decoders import open_image
from image_processing.core.libvips.definitions import Image
from image_processing.core.video.ffmpeg import probe, parser
from image_processing.core import specification


class BaseMediaPassport:
    def __init__(
        self, source_file: Path, mime_type: str, content_type: ContentTypeEnum
    ):
        self.source_file = source_file
        self.mime = mime_type
        self.file_format: FormatEnum = MIME_TYPE_TO_FORMAT[mime_type]
        self.content_type = content_type

    def calc_sha256(self) -> bytes:
        return calc_sha256(self.source_file)

    def calc_xxh3_64(self) -> int:
        return calc_xxh3_64(self.source_file)


class StaticImagePassport(BaseMediaPassport):
    def __init__(self, source_file: Path, mime_type: str):
        super().__init__(source_file, mime_type, ContentTypeEnum.IMAGE)
        self.image: Image = open_image(source_file)
        self.width = self.image.width
        self.height = self.image.height


class VideoPassport(BaseMediaPassport):
    def __init__(
        self,
        source_file: Path,
        mime_type: str,
        vfr_test_data: Optional[tuple[float, bool, int]] = None,
    ):
        self.ffprobe_raw_data = probe(source_file)
        self.video_streams: list[dict] = parser.get_video_streams(
            self.ffprobe_raw_data
        )
        self.audio_streams: list[dict] = parser.find_audio_streams(
            self.ffprobe_raw_data
        )
        self.current_video_stream = self.video_streams[0]
        self.current_audio_stream = None
        if len(self.audio_streams):
            self.current_audio_stream = self.audio_streams[0]
        size_tuple = parser.get_video_size(self.current_video_stream)
        self.width: int = size_tuple[0]
        self.height: int = size_tuple[1]
        self.min_size: int = size_tuple[2]
        self.max_size: int = size_tuple[3]
        self.fps = parser.get_fps(self.current_video_stream)
        self.video_codec: specification.video.VideoCodecs = (
            specification.video.codec_name_to_enum(
                parser.get_codec_name(self.current_video_stream)
            )
        )
        self.audio_codec: Optional[specification.audio.AudioCodecs] = None
        if self.current_audio_stream is not None:
            self.audio_codec = specification.audio.codec_name_to_enum(
                parser.get_codec_name(self.current_audio_stream)
            )
            self.is_mp4_compatible = (
                specification.validation.is_mp4_compatible(
                    self.video_codec, self.audio_codec
                )
            )
            self.is_webm_compatible = (
                specification.validation.is_webm_compatible(
                    self.video_codec, self.audio_codec
                )
            )
        else:
            self.is_mp4_compatible = (
                self.video_codec
                in specification.video.CONTAINER_SUPPORTED_VIDEO_CODECS[
                    specification.containers.VideoContainers.MPEG_4
                ]
            )
            self.is_webm_compatible = (
                self.video_codec
                in specification.video.CONTAINER_SUPPORTED_VIDEO_CODECS[
                    specification.containers.VideoContainers.WEBM
                ]
            )
        self.pixel_format = parser.get_video_pixel_format(
            self.current_video_stream
        )
        raw_duration: Optional[str] = self.ffprobe_raw_data["format"].get(
            "duration", None
        )
        self.duration: Optional[float] = (
            float(raw_duration) if raw_duration is not None else None
        )
        self.has_alpha_channel = parser.has_alpha_channel(self.pixel_format)
        self.bit_depth = (
            specification.video.PIXEL_FORMAT_TO_BITS_PER_CHANNEL.get(
                self.pixel_format, None
            )
        )
        if vfr_test_data is not None:
            self.is_video_loop = parser.test_videoloop(
                self.ffprobe_raw_data, vfr_test_data[0]
            )
        else:
            self.is_video_loop = parser.test_videoloop(self.ffprobe_raw_data)
        content_type = (
            ContentTypeEnum.VIDEO_LOOP
            if self.is_video_loop
            else ContentTypeEnum.VIDEO
        )
        self.is_vfr: Optional[bool] = None
        self.frames_count: Optional[int] = None
        self.estimated_duration: Optional[float] = None

        if vfr_test_data is not None:
            self.estimated_duration, self.is_vfr, self.frames_count = (
                vfr_test_data
            )
        elif self.is_video_loop:
            self.estimated_duration, self.is_vfr, self.frames_count = (
                parser.check_variable_frame_rate_and_estimate_duration(
                    source_file
                )
            )
        self.codec_profile: Optional[str]
        self.codec_level: Optional[int]
        self.codec_profile, self.codec_level = (
            parser.get_profile_and_level_if_exists(self.current_video_stream)
        )
        self.is_unfinalized = False

        super().__init__(source_file, mime_type, content_type)

        if self.duration is None and self.file_format is FormatEnum.WEBM:
            self.is_unfinalized = specification.validation.is_webm_unfinalized(
                self.source_file
            )

    @property
    def codec_string(self) -> str:
        codec_parts = []
        VideoCodecs = specification.video.VideoCodecs
        AudioCodecs = specification.audio.AudioCodecs

        v_str = ""

        if self.video_codec == VideoCodecs.H264:
            v_str = specification.video.get_h264_codec_str(
                self.codec_profile, self.codec_level
            )
        elif self.video_codec == VideoCodecs.VP9:
            v_str = specification.video.get_vp9_codec_str(
                self.codec_profile, self.codec_level, self.bit_depth
            )
        elif self.video_codec == VideoCodecs.AV1:
            v_str = specification.video.get_av1_codec_str(
                self.codec_profile, self.codec_level, self.bit_depth
            )
        elif self.video_codec == VideoCodecs.VP8:
            v_str = specification.video.get_vp8_codec_str()

        if v_str:
            codec_parts.append(v_str)

        if self.current_audio_stream:
            a_profile = self.current_audio_stream.get("profile")
            a_str = ""

            if self.audio_codec == AudioCodecs.AAC and a_profile:
                a_str = specification.audio.get_aac_codec_str(a_profile)
            elif self.audio_codec == AudioCodecs.Opus:
                a_str = specification.audio.get_opus_codec_str()
            elif self.audio_codec == AudioCodecs.Vorbis:
                a_str = specification.audio.get_vorbis_codec_str()

            if a_str:
                codec_parts.append(a_str)

        return ",".join(codec_parts)
