from django.db import models
import pathlib
import enum
from medialib_v2.settings import MEDIALIB_COLLECTION_DIRECTORY

# from medialib_v2 import secrets
from django.core.exceptions import ValidationError

DEBUG = True
REPRESENATION_FILE_PATH_LIMIT = 512


class ContentTypeEnum(enum.StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    VIDEO_LOOP = "video-loop"


class Content(models.Model):
    title = models.TextField(null=True, blank=True)
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
    description = models.TextField(null=True, blank=True)
    addition_date = models.DateTimeField(auto_now_add=True, db_index=True)
    is_hidden = models.BooleanField(default=False)
    last_edit = models.DateTimeField(auto_now=True)
    source_hash = models.BinaryField(
        max_length=32,
        unique=True,
        db_index=True,
        null=True,
        help_text="SHA-256 hash of the original file content (stored as BYTEA).",
    )

    class Meta:
        verbose_name = "content"
        verbose_name_plural = "content"


class ContentOrigin(models.Model):
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    name = models.CharField(max_length=32)
    origin_id = models.TextField("ID on origin")


COMPATIBILITY_LEVEL_MAPPING = [
    (4, "Supercomputer"),
    (3, "Personal Computer"),
    (2, "Mobile device"),
    (1, "Old hardware"),
    (0, "Very old hardware"),
]


class RepresentationTypeEnum(models.IntegerChoices):
    # NOTE: values in range 1-9 reserved for subtypes
    # Audio range: 0-9
    # Image range: 10-19
    # Video range: 20-29
    # For example: SOUNDTRACK = 1
    # or: THUMBNAIL = 12
    AUDIO = 0
    IMAGE = 10
    VIDEO = 20


class Representation(models.Model):
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
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
    repr_type = models.IntegerField(choices=RepresentationTypeEnum, null=False)
    codec_string = models.CharField(max_length=255, null=True, blank=True)

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


class ImageHash(models.Model):
    content = models.OneToOneField(
        Content, on_delete=models.CASCADE, db_index=True
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
    alternate_version = models.BooleanField(default=False, db_index=True)


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


class Tag(models.Model):
    title = models.TextField()
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
    category = models.CharField(choices=CATEGORY_CHOICES, db_index=True)
    content = models.ManyToManyField(Content)
    implications = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="TagImplications",
        through_fields=("target", "implicate"),
        related_name="is_implied_by",
    )

    def __str__(self):
        return f"{self.title} ({self.category})"


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


class TagAlias(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_index=True)
    title = models.TextField(
        unique=True, null=False, blank=False, db_index=True
    )

    class Meta:
        verbose_name = "alias of tag"
        verbose_name_plural = "aliases of tag"


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
