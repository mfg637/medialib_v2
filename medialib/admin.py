import io
from django.contrib import admin
from django import forms
import magic
from . import models as ml_models
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
import pathlib


MOV_MIMETYPE = "video/quicktime"
MPEG4V_MIMETYPE = "video/mp4"
UNDEFINED_MIMETYPE = "application/octet-stream"
PNG_HEADER_SEQUENCE = b"\x89PNG\x0d\x0a\x1a\x0a"
PNG_MIMETYPE = "image/png"


def detect_file_type(chunk: bytes, request_header_mimetype):
    mime = magic.from_buffer(chunk, mime=True)
    if mime == MOV_MIMETYPE and request_header_mimetype == MPEG4V_MIMETYPE:
        mime = MPEG4V_MIMETYPE
    if mime == UNDEFINED_MIMETYPE:
        # check PNG header
        header = chunk[:8]
        if header == PNG_HEADER_SEQUENCE:
            mime = PNG_MIMETYPE
    content_type = None
    is_image = False
    if mime.startswith("image/"):
        is_image = True
        content_type = ml_models.ContentTypeEnum.IMAGE
    if mime.startswith("video/"):
        content_type = ml_models.ContentTypeEnum.VIDEO
    elif mime.startswith("audio/"):
        content_type = ml_models.ContentTypeEnum.AUDIO
    elif is_image:
        pass
    else:
        raise ValidationError("undetected content type, mime: %(mime)s", params={"mime": mime})
    return mime, content_type, is_image


class ContentForm(forms.ModelForm):
    # TODO: set temporary file path
    # resolved: MEDIALIB_ROOT + "/queue"
    # TODO: make image processing task
    media_file = forms.FileField()
    class Meta:
        model = ml_models.Content
        fields = [
            "media_file",
            "title",
            "description",
            "is_hidden",
        ]
        read_only = ["content_type", "addition_date", "last_edit"]

    def clean(self):
        cleaned_data = super().clean()
        mf: UploadedFile = self.cleaned_data["media_file"]
        if cleaned_data["title"] is None:
            cleaned_data["title"] = pathlib.Path(mf.name).stem
        if cleaned_data["description"] == "":
            cleaned_data["description"] = None
        mf.seek(0)
        mime, content_type, is_image = detect_file_type(next(mf.chunks()), mf.content_type)
        mf.seek(0)
        cleaned_data["content_type"] = content_type
        return cleaned_data

    def save(self, commit=True):
        print(self.cleaned_data, type(self.cleaned_data))
        # TODO: implement task processing
        # content = super().save(commit=commit)


#admin.site.register(ContentForm)
class ContentAdmin(admin.ModelAdmin):
    form = ContentForm


admin.site.register(ml_models.Content, ContentAdmin)


class TagAliasAdmin(admin.StackedInline):
    model = ml_models.TagAlias
    list_display = ""


class TagImplicationAdmin(admin.TabularInline):
    model = ml_models.TagImplications
    fk_name = "target"
    autocomplete_fields = ["implicate"]


@admin.register(ml_models.Tag)
class TagAdmin(admin.ModelAdmin):
    inlines = [TagAliasAdmin, TagImplicationAdmin]
    list_display = ["title", "category"]
    list_filter = ["category"]
    search_fields = ["tagalias__title"]

    def save_model(self, request, current_tag: ml_models.Tag, form, change):
        super().save_model(request, current_tag, form, change)
        if not change:  # Only add alias for new tags
            alias_prefix = ""
            if current_tag.category == ml_models.CategoryEnum.CHARACTER:
                alias_prefix = "character:"
            elif current_tag.category == ml_models.CategoryEnum.ARTIST:
                alias_prefix = "artist:"
            elif current_tag.category == ml_models.CategoryEnum.PROMPTER:
                alias_prefix = "prompter:"
            elif current_tag.category == ml_models.CategoryEnum.GENERATOR:
                alias_prefix = "generator:"
            elif current_tag.category == ml_models.CategoryEnum.SET:
                alias_prefix = "set:"
            tag_alias = alias_prefix + current_tag.title.lower()
            ml_models.TagAlias.objects.create(tag=current_tag, title=tag_alias).save()
            if " " in tag_alias:
                ml_models.TagAlias.objects.create(
                    tag=current_tag, title=tag_alias.replace(" ", "_")
                ).save()
