from django.db import models
import pathlib
import enum

# from medialib_v2 import secrets
from django.core.exceptions import ValidationError
from image_processing.models import Task


DEBUG = True


class ContentTypeEnum(enum.StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    VIDEO_LOOP = "video-loop"


class Content(models.Model):
    id = models.BigAutoField(primary_key=True)
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
    (0, "Supercomputer"),
    (1, "Personal Computer"),
    (2, "Mobile device"),
    (3, "Old hardware"),
    (4, "Very old hardware"),
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
    id = models.BigAutoField(primary_key=True)
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    filepath = models.FilePathField(unique=True, null=False)
    format = models.CharField(max_length=12)
    compatibility_level = models.PositiveSmallIntegerField(
        "Compatibility level", choices=COMPATIBILITY_LEVEL_MAPPING
    )
    generation_date = models.DateTimeField(
        "Date of creation", auto_now_add=True
    )
    width = models.PositiveSmallIntegerField(null=True)
    height = models.PositiveSmallIntegerField(null=True)
    repr_type = models.IntegerField(choices=RepresentationTypeEnum)

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
        if not DEBUG:
            _filepath = pathlib.Path(str(self.filepath))
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class Attachments(models.Model):
    id = models.BigAutoField(primary_key=True)
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


class ContentToTaskRelationship(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, db_index=True)


class ImageHash(models.Model):
    id = models.BigAutoField(primary_key=True)
    content = models.OneToOneField(
        Content, on_delete=models.CASCADE, db_index=True
    )
    aspect_ratio = models.FloatField("Aspect Ratio")
    value_hash = models.BinaryField(
        "Value component hash", max_length=256, db_index=True
    )
    hue_hash = models.BigIntegerField("Hue component hash", db_index=True)
    saturation_hash = models.BigIntegerField(
        "Saturation component hash", db_index=True
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
    id = models.BigAutoField(primary_key=True)
    title = models.TextField()
    CATEGORY_CHOICES = [
        (CategoryEnum.ARTIST, "Artist"),
        (CategoryEnum.PROMPTER, "Prompter"),
        (CategoryEnum.GENERATOR, "AI Generation model"),
        (CategoryEnum.SET, "Unordered set"),
        (CategoryEnum.COPYRIGHT, "Copyright"),
        (CategoryEnum.RATING, "Rating"),
        (CategoryEnum.SPECIES, "Species"),
        (CategoryEnum.CHARACTER, "Character name"),
        (CategoryEnum.GENDER, "Gender"),
        (CategoryEnum.CONTENT, "Content description"),
    ]
    category = models.CharField(choices=CATEGORY_CHOICES, db_index=True)

    def __str__(self):
        return f"{self.title} ({self.category})"


class TagImplications(models.Model):
    id = models.BigAutoField(primary_key=True)
    target = models.ForeignKey(
        Tag, on_delete=models.CASCADE, db_index=True, related_name="target_tag"
    )
    implicate = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="implicated_tag"
    )

    def clean_fields(self, exclude=...):
        if self.target.id == self.implicate.id:
            raise ValidationError("Tag can't implicate itself")
        return super().clean_fields(exclude)

    class Meta:
        verbose_name = "implication of tag"
        verbose_name_plural = "implications of tag"
        constraints = [
            models.UniqueConstraint(
                fields=["target", "implicate"], name="unique_tag_to_implication"
            )
        ]


class TagAlias(models.Model):
    id = models.BigAutoField(primary_key=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_index=True)
    title = models.TextField(
        unique=True, null=False, blank=False, db_index=True
    )

    class Meta:
        verbose_name = "alias of tag"
        verbose_name_plural = "aliases of tag"


class ContentToTagsRelationship(models.Model):
    id = models.BigAutoField(primary_key=True)
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content", "tag"], name="unique_tag_to_content"
            )
        ]


class Album(models.Model):
    id = models.AutoField(primary_key=True)
    album_set = models.ForeignKey(
        Tag, on_delete=models.PROTECT, related_name="album_set"
    )
    artist_set = models.ForeignKey(
        Tag, on_delete=models.PROTECT, related_name="artist_tag"
    )

    def clean(self):
        if self.album_set.category != "set":
            raise ValidationError("album_set_id must have the 'set' category.")
        if self.artist_set.category != "artist":
            raise ValidationError(
                "artist_set_id must have the 'artist' category."
            )
        super().clean()


class AlbumOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
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
