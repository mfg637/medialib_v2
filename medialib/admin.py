from django.contrib import admin
from django import forms
from . import models as ml_models
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
import pathlib


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
        # TODO: content type detection
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
