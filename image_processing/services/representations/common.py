import pathlib
import dataclasses
from typing import Optional
from base.shared_enums.medialib_model import RepresentationTypeEnum
from base.shared_knowledge.file_format import FormatEnum


@dataclasses.dataclass(frozen=True)
class Representation:
    compatibility_level: int
    file_path: pathlib.Path
    width: Optional[int]
    height: Optional[int]
    repr_type: RepresentationTypeEnum
    _format: FormatEnum
    codec_string: Optional[str] = None
