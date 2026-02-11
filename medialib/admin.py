from django.contrib import admin
from django import forms
from . import models as ml_models
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from base.shared_knowledge.tags import generate_aliases
from pathlib import Path


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
            aliases = generate_aliases(
                current_tag.title, current_tag.get_category()
            )
            for alias in aliases:
                ml_models.TagAlias.objects.create(tag=current_tag, title=alias)


class RepresentationInline(admin.TabularInline):
    model = ml_models.Representation
    extra = 0
    readonly_fields = [
        "filepath",
        "format",
        "width",
        "height",
        "repr_type",
        "compatibility_level",
        "codec_string",
    ]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ImageHashInline(admin.StackedInline):
    model = ml_models.ImageHash
    readonly_fields = [
        "aspect_ratio",
        "display_L_hash",
        "display_a_hash",
        "display_b_hash",
    ]
    can_delete = False
    extra = 0

    def display_L_hash(self, obj):
        return obj.L_hash.tobytes().hex() if obj.L_hash else "-"

    display_L_hash.short_description = "L Hash"

    def display_a_hash(self, obj):
        return obj.a_hash.tobytes().hex() if obj.a_hash else "-"

    display_a_hash.short_description = "a Hash"

    def display_b_hash(self, obj):
        return obj.b_hash.tobytes().hex() if obj.b_hash else "-"

    display_b_hash.short_description = "b Hash"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ml_models.Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ["title", "content_type", "is_hidden", "addition_date"]
    list_filter = ["content_type", "is_hidden"]
    search_fields = ["title", "description", "source_hash"]

    readonly_fields = [
        "content_type",
        "formatted_hash",
        "addition_date",
        "last_edit",
    ]

    autocomplete_fields = ["tags"]

    inlines = [RepresentationInline, ImageHashInline]

    def formatted_hash(self, obj):
        if obj.source_hash:
            return obj.source_hash.tobytes().hex()
        return "-"

    formatted_hash.short_description = "Source Hash"

    fieldsets = [
        (None, {"fields": ["title", "description", "is_hidden", "tags"]}),
        (
            "Technical Metadata",
            {
                "fields": [
                    "content_type",
                    "formatted_hash",
                    "addition_date",
                    "last_edit",
                ],
                "classes": ["collapse"],
            },
        ),
    ]


# admin.site.register(ml_models.Content, ContentAdmin)
