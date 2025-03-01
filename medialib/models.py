from django.db import models
import pathlib
import enum
from medialib_v2 import secrets
from django.core.exceptions import ValidationError


DEBUG = True


class Content(models.Model):
    id = models.BigAutoField(primary_key=True)
    filepath = models.FilePathField(
        str(secrets.MEDIALIB_HOME_DIR),
        recursive=True,
        allow_folders=True,
        unique=True,
        null=False
    )
    title = models.CharField(max_length=64, null=True)
    CONTENT_TYPE_MAPPING = [
        ("image", "Image"),
        ("audio", "Audio"),
        ("video", "Video"),
        ("video-loop", "Video-loop")
    ]
    content_type = models.CharField(choices=CONTENT_TYPE_MAPPING, max_length=10)
    description = models.TextField(null=True)
    addition_date = models.DateTimeField(auto_now_add=True, db_index=True)
    is_hidden = models.BooleanField(default=False)
    last_edit = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        if not DEBUG:
            # TODO: implement manifest files handling (.srs and .mpd)
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class ContentOrigin(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=32)
    origin_id = models.CharField("ID on origin", max_length=128)


class Thumbnail(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE, db_index=True)
    filepath = models.FilePathField(str(secrets.MEDIALIB_THUMBNAILS_DIR), unique=True, )
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    generation_date = models.DateTimeField("Date of generation", auto_now_add=True)
    format = models.CharField(max_length=12)

    def delete(self, *args, **kwargs):
        if not DEBUG:
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


COMPATIBILITY_LEVEL_MAPPING = [
    (0, "Supercomputer"),
    (1, "Personal Computer"),
    (2, "Powerfull mobile device"),
    (3, "Dated mobile device"),
    (4, "Old hardware")
]


class Representation(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE, db_index=True)
    filepath = models.FilePathField(
        str(secrets.MEDIALIB_HOME_DIR),
        recursive=True,
        allow_folders=True,
        unique=True,
        null=False
    )
    format = models.CharField(max_length=12)
    compatibility_level = models.PositiveSmallIntegerField(
        "Compatibility level",
        choices=COMPATIBILITY_LEVEL_MAPPING
    )

    def delete(self, *args, **kwargs):
        if not DEBUG:
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class Attachments(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE, db_index=True)
    filepath = models.FilePathField(
        str(secrets.MEDIALIB_HOME_DIR),
        recursive=True,
        allow_folders=True,
        unique=True,
        null=False,
        db_index=True
    )
    title = models.CharField(max_length=64)
    format = models.CharField(max_length=12)

    def delete(self, *args, **kwargs):
        if not DEBUG:
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class ImageHash(models.Model):
    content_id = models.OneToOneField(Content, on_delete=models.CASCADE, db_index=True)
    aspect_ratio = models.FloatField("Aspect Ratio")
    value_hash = models.BinaryField("Value component hash", max_length=256, db_index=True)
    hue_hash = models.BigIntegerField("Hue component hash", db_index=True)
    saturation_hash = models.BigIntegerField("Saturation component hash", db_index=True)
    alternate_version = models.BooleanField(default=False, db_index=True)


class Tag(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=240)
    CATEGORY_CHOICES = [
        ("artist", "Artist"),
        ("prompter", "Prompter"),
        ("generator", "AI Generation model"),
        ("set", "Unordered set"),
        ("copyright", "Copyright"),
        ("rating", "Rating"),
        ("species", "Species"),
        ("character", "Character name"),
        ("content", "Content description")
    ]
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)


class TagImplications(models.Model):
    target = models.ForeignKey(
        Tag, on_delete=models.CASCADE, db_index=True, related_name="target_tag"
    )
    implicate = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="implicated_tag"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["target", "implicate"],
                name="unique_tag_to_implication"
            )
        ]


class TagAlias(models.Model):
    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(
        max_length=255, unique=True, null=False, blank=False, db_index=True
    )


class ContentToTagsRelationship(models.Model):
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    tag_id = models.ForeignKey(
        Tag, on_delete=models.CASCADE, db_index=True
    )


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_id", "tag_id"],
                name="unique_tag_to_content"
            )
        ]


class Album(models.Model):
    id = models.AutoField(primary_key=True)
    album_set_id = models.ForeignKey(
        Tag, on_delete=models.PROTECT, related_name="album_set"
    )
    artist_set_id = models.ForeignKey(
        Tag, on_delete=models.PROTECT, related_name="artist_tag"
    )

    def clean(self):
        if self.album_set_id.category != "set":
            raise ValidationError("album_set_id must have the 'set' category.")
        if self.artist_set_id.category != "artist":
            raise ValidationError("artist_set_id must have the 'artist' category.")


class AlbumOrder(models.Model):
    album_id = models.ForeignKey(
        Album, on_delete=models.CASCADE, db_index=True
    )
    content_id = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["album_id", "content_id",],
                name="unique_content_to_album"
            )
        ]