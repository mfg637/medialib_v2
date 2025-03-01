from django.contrib import admin
from django import forms
from . import models as ml_models

# Register your models here.
admin.site.register(ml_models.Content)


class TagAliasAdmin(admin.StackedInline):
    model = ml_models.TagAlias
    list_display = ""


class TagImplicationAdmin(admin.TabularInline):
    model = ml_models.TagImplications
    fk_name = "target"


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
