import enum
from os import cpu_count
import pathlib


class YUV4MPEG2_LIMITED_RANGE_CORRENTION_MODES(enum.Enum):
    NONE = enum.auto()
    CLIPPING = enum.auto()
    EXPAND = enum.auto()


yuv4mpeg2_limited_range_correction = YUV4MPEG2_LIMITED_RANGE_CORRENTION_MODES.CLIPPING

encoding_threads = cpu_count()

gop_length_seconds = 10

avifenc_encoding_speed = 2

samples_root_dir = pathlib.Path("image_processing/tests/decoding/samples")