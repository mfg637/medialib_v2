import pathlib
import dataclasses
import enum
from typing import Optional
from image_processing.core.file_format import FormatEnum

# from medialib.models import RepresentationTypeEnum


# временный дубликат medialib.models.RepresentationTypeEnum
# прототип придётся удалить в будущем.
# существование прототипа затрудняет поддержку кода в чистоте
class RepresentationTypeEnum(enum.IntEnum):
    # NOTE: values in range 1-9 reserved for subtypes
    # Audio range: 0-9
    # Image range: 10-19
    # Video range: 20-29
    # For example: SOUNDTRACK = 1
    # or: THUMBNAIL = 12
    AUDIO = 0
    IMAGE = 10
    VIDEO = 20


@dataclasses.dataclass(frozen=True)
class Representation:
    compatibility_level: int
    file_path: pathlib.Path
    width: Optional[int]
    height: Optional[int]
    repr_type: RepresentationTypeEnum
    _format: FormatEnum
    codec_string: Optional[str] = None
