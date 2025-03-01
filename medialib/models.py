from django.db import models
import pathlib
import enum
from medialib_v2 import secrets


DEBUG = True


class Content(models.Model):
    id = models.BigAutoField()
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
    addition_date = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False)
    last_edit = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        if not DEBUG:
            # TODO: implement manifest files handling (.srs and .mpd)
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class ContentOrigin(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    origin_id = models.CharField("ID on origin", max_length=128)


class Thumbnail(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
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
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
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
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
    filepath = models.FilePathField(
        str(secrets.MEDIALIB_HOME_DIR),
        recursive=True,
        allow_folders=True,
        unique=True,
        null=False
    )
    title = models.CharField(max_length=64)
    format = models.CharField(max_length=12)

    def delete(self, *args, **kwargs):
        if not DEBUG:
            _filepath = pathlib.Path(self.filepath)
            _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)


class ImageHash(models.Model):
    content_id = models.OneToOneField(Content, on_delete=models.CASCADE)
    aspect_ratio = models.FloatField("Aspect Ratio")
    value_hash = models.BinaryField("Value component hash", max_length=256)
    hue_hash = models.BigIntegerField("Hue component hash")
    saturation_hash = models.BigIntegerField("Saturation component hash")
    alternate_version = models.BooleanField(default=False)


class Tag(models.Model):
    id = models.BigAutoField()
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
    target = models.ForeignKey(Tag, on_delete=models.CASCADE)
    implicate = models.ForeignKey(Tag, on_delete=models.CASCADE)


class TagAlias(models.Model):
    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, unique=True, null=False, blank=False)


class ContentToTagsRelationship(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE)


class Album(models.Model):
    id = models.AutoField()
    album_set_id = models.ForeignKey(Tag, on_delete=models.PROTECT)
    artist_set_id = models.ForeignKey(Tag, on_delete=models.PROTECT)


class AlbumOrder(models.Model):
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE)
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
    order = models.IntegerField()