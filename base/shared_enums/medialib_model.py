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


class CategoryEnum(enum.StrEnum):
    CREATOR = "creator"
    ARTIST = "artist"
    PROMPTER = "prompter"
    AI = "ai"
    SET = "set"
    COMIC = "comic"
    COPYRIGHT = "copyright"
    RATING = "rating"
    SPECIES = "species"
    CHARACTER = "character"
    CHARACTER_GROUP = "character-group"
    GENDER = "gender"
    LORE = "lore"
    META = "meta"
    ERROR = "error"
    STYLE = "style"
    CONTENT = "content"
