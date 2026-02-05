import enum
from django.db.models import IntegerChoices


class ContentTypeEnum(enum.StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    VIDEO_LOOP = "video-loop"


class RepresentationTypeEnum(IntegerChoices):
    # NOTE: values in range 1-9 reserved for subtypes
    # Audio range: 0-9
    # Image range: 10-19
    # Video range: 20-29
    # For example: SOUNDTRACK = 1
    # or: THUMBNAIL = 12
    AUDIO = 0
    IMAGE = 10
    VIDEO = 20
