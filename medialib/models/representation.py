from django.db import models
from django.core.exceptions import ValidationError
from medialib_v2.settings import MEDIALIB_COLLECTION_DIRECTORY
from base.shared_enums.medialib_model import (
    RepresentationTypeEnum,
)
from base.shared_knowledge import file_format
from .base import (
    REPRESENATION_FILE_PATH_LIMIT,
    COMPATIBILITY_LEVEL_MAPPING,
    REPRESENTATION_TYPE_MAPPING,
    REPRESENTATION_TYPE_DICT,
)
from .content import Content


class Representation(models.Model):
    id: int
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="representation_set",
    )
    filepath = models.FileField(
        upload_to=str(MEDIALIB_COLLECTION_DIRECTORY.joinpath("%Y/%m/%d/")),
        unique=True,
        null=False,
        max_length=REPRESENATION_FILE_PATH_LIMIT,
    )
    format = models.CharField(max_length=12)
    compatibility_level = models.PositiveSmallIntegerField(
        "Compatibility level", choices=COMPATIBILITY_LEVEL_MAPPING
    )
    generation_date = models.DateTimeField(
        "Date of creation", auto_now_add=True
    )
    width = models.PositiveSmallIntegerField(null=True)
    height = models.PositiveSmallIntegerField(null=True)
    repr_type = models.IntegerField(
        choices=REPRESENTATION_TYPE_MAPPING, null=False
    )
    codec_string = models.CharField(max_length=255, blank=True, default="")
    hash = models.BigIntegerField(null=False, default=None)

    def get_type(self) -> RepresentationTypeEnum:
        return RepresentationTypeEnum(self.repr_type)

    def get_type_string(self) -> str:
        return REPRESENTATION_TYPE_DICT[self.repr_type]

    def check_side_size_limit(self, size_limit: int) -> bool:
        return self.width <= size_limit and self.height <= size_limit

    def get_mime_type(self):
        return file_format.MIME_BY_EXTENSION[f".{self.format}"]

    def get_size_relation(self, target_w, target_h) -> float:
        if self.width is None or self.height is None:
            raise Exception("Representation has no width or height")
        if self.width * target_h >= target_w * self.height:
            return self.width / target_w
        else:
            return self.height / target_h

    @property
    def get_portrait_thumb_medium_relation(self):
        return self.get_size_relation(192, 256)

    @property
    def get_thumb_small_relation(self):
        return self.get_size_relation(128, 128)

    def clean(self):
        if self.repr_type >= RepresentationTypeEnum.IMAGE:
            errors = {}
            if self.width is None or self.width <= 0:
                errors["width"] = "Required for image/video and must be > 0"
            if self.height is None or self.height <= 0:
                errors["height"] = "Required for image/video and must be > 0"
            if errors:
                raise ValidationError(errors)
        super().clean()

    def delete(self, *args, **kwargs):
        if hasattr(self, "filepath") and self.filepath:
            self.filepath.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self) -> str:
        if self.width and self.height:
            return (
                f"Representation content id = {self.content.id}, "
                f"file path: {self.filepath}, "
                f"compatibility level: {self.compatibility_level}, "
                f"format: {self.format}, "
                f"type: {self.get_type_string()}, "
                f"size: {self.width}x{self.height}"
            )
        return (
            f"Representation content id = {self.content.id}, "
            f"file path: {self.filepath}, "
            f"compatibility level: {self.compatibility_level}, "
            f"format: {self.format}, "
            f"type: {self.repr_type}"
        )
