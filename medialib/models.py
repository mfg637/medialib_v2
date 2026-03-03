from django.db import models
from django.utils import timezone
import pathlib
from medialib_v2.settings import MEDIALIB_COLLECTION_DIRECTORY
from base.shared_enums.medialib_model import (
    ContentTypeEnum,
    RepresentationTypeEnum,
    CategoryEnum,
)
from base.shared_knowledge import origin, file_format

# from medialib_v2 import secrets
from django.core.exceptions import ValidationError

DEBUG = True
REPRESENATION_FILE_PATH_LIMIT = 512
TAG_NAME_LENGTH_LIMIT = 512
TAG_ALIAS_LENGRG_LIMIT = TAG_NAME_LENGTH_LIMIT


class Content(models.Model):
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
    SOURCE_HASH_BINARY_LENGTH = 32
    source_hash = models.BinaryField(
        max_length=SOURCE_HASH_BINARY_LENGTH,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of the original file content (stored as BYTEA).",
    )
    tags = models.ManyToManyField(
        "Tag", related_name="content_set", blank=True
    )
    YEAR_DIGITS = 4
    MONTH_DAY_DIGITS = 2
    SOURCE_HASH_HEX_LENGTH = SOURCE_HASH_BINARY_LENGTH * 2
    HYPHEN_COUNT = 3
    SLUG_LENGTH = (
        YEAR_DIGITS
        + MONTH_DAY_DIGITS * 2
        + SOURCE_HASH_HEX_LENGTH
        + HYPHEN_COUNT
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


class ContentOrigin(models.Model):
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="origin_set",
    )
    name = models.CharField(max_length=32)
    origin_id = models.CharField(
        "ID on origin", max_length=255, blank=True, default=""
    )
    alternate = models.BooleanField(default=False)

    def get_url_if_possible(self) -> str:
        if self.origin_id is None:
            return ""
        origin_type = origin.get_origin_type(self.name)
        if origin_type is None:
            return ""
        origin_class: origin.AbstractOriginType = origin_type()
        return origin_class.generate_url(self.origin_id)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "origin_id"],
                name="unique_origin_source_id",
                condition=~models.Q(origin_id=""),
            )
        ]
        indexes = [models.Index(fields=["name", "origin_id"])]


COMPATIBILITY_LEVEL_MAPPING = [
    (4, "CL4 Supercomputer"),
    (3, "CL3 Personal Computer"),
    (2, "CL2 Mobile device"),
    (1, "CL1 Old hardware"),
    (0, "CL0 Very old hardware"),
]
COMPATIBILITY_LEVEL_DICT: dict[int, str] = {
    CL[0]: CL[1] for CL in COMPATIBILITY_LEVEL_MAPPING
}
REPRESENTATION_TYPE_MAPPING = [
    (RepresentationTypeEnum.IMAGE.value, "Image"),
    (RepresentationTypeEnum.VIDEO.value, "Video"),
    (RepresentationTypeEnum.AUDIO.value, "Audio"),
]
REPRESENTATION_TYPE_DICT: dict[int, str] = {
    repr_type[0]: repr_type[1] for repr_type in REPRESENTATION_TYPE_MAPPING
}


class Representation(models.Model):
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

    def get_type(self) -> RepresentationTypeEnum:
        return RepresentationTypeEnum(self.repr_type)

    def get_type_string(self) -> str:
        return REPRESENTATION_TYPE_DICT[self.repr_type]

    def check_side_size_limit(self, size_limit: int) -> bool:
        return self.width <= size_limit and self.height <= size_limit

    def get_mime_type(self):
        return file_format.MIME_BY_EXTENSION[f".{self.format}"]

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


class Attachments(models.Model):
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    filepath = models.FilePathField(unique=True, null=False, db_index=True)
    title = models.CharField(max_length=64)
    format = models.CharField(max_length=12)

    def delete(self, *args, **kwargs):
        if not DEBUG:
            _filepath = pathlib.Path(str(self.filepath))
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)

    def __str__(self):
        return (
            f"Attachments content id: {self.content.id}, "
            f"filepath: {self.filepath}, "
            f"title={self.title}, "
            f"format: {self.format}"
        )


class ImageHash(models.Model):
    content = models.OneToOneField(
        Content,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="imagehash",
    )
    aspect_ratio = models.FloatField("Aspect Ratio")
    L_hash = models.BinaryField(
        "Lightness component hash", max_length=32, db_index=True
    )
    a_hash = models.BinaryField(
        "a* component hash", max_length=8, db_index=True
    )
    b_hash = models.BinaryField(
        "b* component hash", max_length=8, db_index=True
    )
    search_similar = models.BinaryField(
        max_length=8, db_index=True, null=False
    )
    far_similarity = models.BinaryField(
        max_length=4, db_index=True, null=False
    )
    alternate_version = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["L_hash", "a_hash", "b_hash"]),
        ]

    def save(self, *args, **kwargs):
        if not (self.L_hash and self.a_hash and self.b_hash):
            raise ValidationError(
                f"ImageHash for content {self.content.id} cannot be saved with empty hash fields. "
                f"L: {len(self.L_hash)}b, a: {len(self.a_hash)}b, b: {len(self.b_hash)}b"
            )

        self.search_similar = (
            bytes(self.L_hash)[:4]
            + bytes(self.a_hash)[:2]
            + bytes(self.b_hash)[:2]
        )
        self.far_similarity = (
            bytes(self.L_hash)[:2]
            + bytes(self.a_hash)[:1]
            + bytes(self.b_hash)[:1]
        )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"ImageHash content id {self.content.id}, "
            f"aspect ratio: {self.aspect_ratio}, "
            f"L hash: {self.L_hash.hex()}, "
            f"a hash: {self.a_hash.hex()}, "
            f"b hash: {self.b_hash.hex()}, "
            f"alternate version: {self.alternate_version}"
        )


class Tag(models.Model):
    title = models.CharField(
        max_length=TAG_NAME_LENGTH_LIMIT, null=False, blank=False
    )
    CATEGORY_CHOICES = [
        (CategoryEnum.CREATOR, "Content creator"),
        (CategoryEnum.ARTIST, "Artist"),
        (CategoryEnum.PROMPTER, "Prompter"),
        (CategoryEnum.AI, "AI related metadata"),
        (CategoryEnum.SET, "Unordered set"),
        (CategoryEnum.COMIC, "Comic pages set"),
        (CategoryEnum.COPYRIGHT, "Copyright"),
        (CategoryEnum.RATING, "Rating"),
        (CategoryEnum.SPECIES, "Species"),
        (CategoryEnum.CHARACTER, "Character name"),
        (CategoryEnum.CHARACTER_GROUP, "Group of characters"),
        (CategoryEnum.GENDER, "Gender"),
        (CategoryEnum.LORE, "Lore metadata"),
        (CategoryEnum.META, "Metadata"),
        (CategoryEnum.ERROR, "Error"),
        (CategoryEnum.STYLE, "Style description"),
        (CategoryEnum.CONTENT, "Content description"),
    ]
    category = models.CharField(
        choices=CATEGORY_CHOICES,
        db_index=True,
        default=CategoryEnum.CONTENT.value,
    )
    implications = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="TagImplications",
        through_fields=("target", "implicate"),
        related_name="is_implied_by",
    )

    def get_category(self: Tag) -> CategoryEnum:
        return CategoryEnum(self.category)

    def __str__(self):
        return f"Tag: {self.title} ({self.category})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "category"],
                name="unique_tag_title_category",
            )
        ]


class TagImplications(models.Model):
    target_id: int
    implicate_id: int
    target = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="implications_target",
    )
    implicate = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="implications_implicated"
    )

    def clean(self):
        if self.target_id == self.implicate_id:
            raise ValidationError("Tag can't implicate itself")
        return super().clean()

    class Meta:
        verbose_name = "implication of tag"
        verbose_name_plural = "implications of tag"
        constraints = [
            models.UniqueConstraint(
                fields=["target", "implicate"],
                name="unique_tag_to_implication",
            )
        ]

    def __str__(self) -> str:
        return (
            "TagImplications target: "
            f"{self.target}, implicates: {self.implicate}"
        )


class TagAlias(models.Model):
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, db_index=True, related_name="alias_set"
    )
    title = models.CharField(
        unique=True,
        null=False,
        blank=False,
        db_index=True,
        max_length=TAG_ALIAS_LENGRG_LIMIT,
    )

    class Meta:
        verbose_name = "alias of tag"
        verbose_name_plural = "aliases of tag"

    def __str__(self) -> str:
        return f"TagAlias: {self.title}, tag id: {self.tag.id}"


class Album(models.Model):
    album_set = models.ForeignKey(
        Tag, on_delete=models.PROTECT, related_name="album_set", null=True
    )
    creator_tags = models.ManyToManyField(Tag, related_name="creator_albums")
    album_name = models.TextField(null=True)
    contents = models.ManyToManyField(
        Content,
        through="AlbumOrder",
        through_fields=("album", "content"),
        related_name="albums",
    )

    def clean(self):
        if self.album_set is not None and self.album_set.category not in {
            CategoryEnum.SET,
            CategoryEnum.COMIC,
        }:
            raise ValidationError("album_set must have the 'set' category.")
        if self.pk:
            valid_categories = {
                CategoryEnum.CREATOR,
                CategoryEnum.ARTIST,
                CategoryEnum.PROMPTER,
            }

            invalid_creators = self.creator_tags.exclude(
                category__in=valid_categories
            )

            if invalid_creators.exists():
                raise ValidationError(
                    (
                        "All creator_tags must belong "
                        "to one on this categories: "
                        "creator/artist/prompter."
                    )
                )
        super().clean()

    def get_album_name(self) -> str:
        if self.album_name is not None:
            return self.album_name
        elif self.album_set is not None:
            return self.album_set.title
        else:
            return "untitled"

    def get_creator_string(self) -> str:
        creator_titles = list(
            self.creator_tags.values_list("title", flat=True)
        )

        if not creator_titles:
            return "Unknown Creators"

        return " and ".join(creator_titles)

    def __str__(self):
        return f"{self.get_album_name()} by {self.get_creator_string()}"


class AlbumOrder(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, db_index=True)
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "album",
                    "content",
                ],
                name="unique_content_to_album",
            )
        ]
        unique_together = (("album", "order"),)

    def __str__(self) -> str:
        return (
            f"AlbumOrder album id: {self.album.id}, "
            f"content id: {self.content.id}, "
            f"order: {self.order}"
        )
