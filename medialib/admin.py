from django.contrib import admin
from . import models as ml_models
from base.shared_knowledge.tags import generate_aliases
from medialib_v2.settings import MEDIA_URL
from django.utils.safestring import mark_safe
from django.urls import reverse


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
    list_display = ["title", "category", "aliases_count"]
    list_filter = ["category"]
    search_fields = ["title", "alias_set__title"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("alias_set")

    def aliases_count(self, obj):
        return obj.alias_set.count()

    aliases_count.short_description = "Aliases"

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
    list_display = [
        "content_thumbnail",
        "title_short",
        "content_type",
        "is_visible",
        "addition_date",
    ]
    list_filter = ["content_type", "is_hidden", "addition_date"]
    search_fields = ["title", "tags__title"]

    readonly_fields = [
        "view_on_site_link",
        "content_preview",
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

    def abstract_representation(self, obj, size_limit, substitute_text):
        repr_list = obj.representation_set.filter(
            repr_type=ml_models.RepresentationTypeEnum.IMAGE.value
        ).order_by("width")
        rep = None
        for current_repr in repr_list:
            if current_repr.check_side_size_limit(size_limit):
                rep = current_repr

        if rep and rep.filepath:
            url = f"/{MEDIA_URL}{rep.filepath}"
            return mark_safe(
                (
                    f'<img src="{url}" '
                    f'style="max-width: {size_limit}px; max-height: {size_limit}px;"'
                    " />"
                )
            )
        return substitute_text

    def content_preview(self, obj):
        return self.abstract_representation(obj, 512, "No preview available")

    content_preview.short_description = "Preview"

    def content_thumbnail(self, obj):
        return self.abstract_representation(obj, 128, "No image")

    content_thumbnail.short_description = "Pic"

    def is_visible(self, obj) -> bool:
        return not bool(obj.is_hidden)

    is_visible.short_description = "Visible"
    is_visible.boolean = True

    def title_short(self, obj: ml_models.Content) -> str:
        LENGTH_LIMIT = 16
        if len(obj.title) > LENGTH_LIMIT:
            return f"{obj.title[:16]}…"
        else:
            return obj.title

    title_short.short_description = "Title"
    title_short.admin_order_field = "title"

    def view_on_site_link(self, obj):
        if obj.slug:
            try:
                url = reverse(
                    "content-info", kwargs={"content_slug": obj.slug}
                )
                return mark_safe(
                    f'<a href="{url}" target="_blank">Visit on site</a>'
                )
            except Exception:
                return "routing error"
        return "-"

    view_on_site_link.short_description = "Link"

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "content_preview",
                    "title",
                    "description",
                    "is_hidden",
                    "tags",
                    "view_on_site_link",
                ]
            },
        ),
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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("tags", "representation_set")
        )


# admin.site.register(ml_models.Content, ContentAdmin)
