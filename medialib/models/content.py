from typing import TYPE_CHECKING
from django.db import models
from django.utils import timezone
from base.shared_enums.medialib_model import (
    ContentTypeEnum,
)
from .base import (
    SOURCE_HASH_BINARY_LENGTH,
    SLUG_LENGTH,
)

if TYPE_CHECKING:
    from .representation import Representation
    from .origin import ContentOrigin
    from .attachment import Attachments
    from .image_hash import ImageHash
    from .metadata import Tag
    from .content_set import AlbumOrder, Collection


class Content(models.Model):
    id: int
    representation_set: models.Manager["Representation"]
    origin_set: models.Manager["ContentOrigin"]
    imagehash: models.Manager["ImageHash"]
    album_item: models.Manager["AlbumOrder"]
    in_collection: models.Manager["Collection"]
    redirects: models.Manager["ContentRedirect"]
    attachments_set: models.Manager["Attachments"]
    tags: models.ManyToManyField["Tag", Content]

    title = models.TextField(blank=True, default="")
    CONTENT_TYPE_MAPPING = [
        (ContentTypeEnum.IMAGE, "Image"),
        (ContentTypeEnum.AUDIO, "Audio"),
        (ContentTypeEnum.VIDEO, "Video"),
        (ContentTypeEnum.VIDEO_LOOP, "Video-loop"),
    ]
    # filepath field removed, because it's redundant
    # media content must have representations
    content_type = models.CharField(
        choices=CONTENT_TYPE_MAPPING,
        max_length=10,
        default=ContentTypeEnum.IMAGE,
    )
    description = models.TextField(blank=True, default="")
    addition_date = models.DateTimeField(auto_now_add=True, db_index=True)
    is_hidden = models.BooleanField(default=False)
    last_edit = models.DateTimeField(auto_now=True)

    source_hash = models.BinaryField(
        max_length=SOURCE_HASH_BINARY_LENGTH,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of the original file content (stored as BYTEA).",
    )
    tags = models.ManyToManyField(
        "Tag", related_name="content_set", blank=True
    )

    slug = models.SlugField(
        max_length=SLUG_LENGTH, unique=True, blank=True, db_index=True
    )

    def generate_slug(self):
        date = self.addition_date or timezone.now()
        date_part = date.strftime("%Y-%m-%d")
        hash_part = self.source_hash.tobytes().hex()
        return f"{date_part}-{hash_part}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_slug()

        super().save(*args, **kwargs)

    def get_content_type(self) -> ContentTypeEnum:
        return ContentTypeEnum(self.content_type)

    def __str__(self) -> str:
        return (
            f"Content id: {self.id}, "
            f"type: {self.content_type}, "
            f"title={self.title}, "
            f"is_hidden = {self.is_hidden}"
        )

    class Meta:
        verbose_name = "content"
        verbose_name_plural = "content"


class ContentRedirect(models.Model):
    id: int
    old_slug = models.SlugField(
        max_length=SLUG_LENGTH, unique=True, db_index=True
    )
    new_content = models.ForeignKey(
        Content, on_delete=models.PROTECT, related_name="redirects"
    )
    created_at = models.DateTimeField(null=False)
    source_hash = models.BinaryField(
        max_length=SOURCE_HASH_BINARY_LENGTH,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of the original file content (stored as BYTEA).",
    )

    def __str__(self):
        return f"Redirect: {self.old_slug} -> {self.new_content.id}"
