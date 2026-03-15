import requests
from django.contrib import admin, messages
from django.shortcuts import redirect

from base.shared_enums.medialib_model import (
    CategoryEnum,
    RepresentationTypeEnum,
)
from . import models as ml_models
from base.shared_knowledge.tags import generate_aliases
from .tags import smart_tag_search
from .tags.tags_processing import resolve_tag, get_all_implications
from medialib_v2.settings import MEDIA_URL
from django.utils.safestring import mark_safe
from django.urls import reverse, path
from .forms import AlbumAdminForm
from django.template.response import TemplateResponse


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
    list_display = ["title", "category", "aliases_count", "content_count"]
    list_filter = ["category"]
    search_fields = ["title", "alias_set__title"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("alias_set")

    def aliases_count(self, obj):
        return obj.alias_set.count()

    aliases_count.short_description = "Aliases"

    def content_count(self, obj):
        return obj.content_set.count()

    content_count.short_description = "Content count"

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return super().get_search_results(request, queryset, search_term)

        queryset = smart_tag_search(search_term, queryset)
        return queryset, False

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
    change_form_template = "admin/medialib/content/change_form.djhtml"
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

    @staticmethod
    def get_image_representation(obj, size_limit):
        repr_list = obj.representation_set.filter(
            repr_type=ml_models.RepresentationTypeEnum.IMAGE.value
        ).order_by("width")
        rep = None
        for current_repr in repr_list:
            if current_repr.check_side_size_limit(size_limit):
                rep = current_repr
        return rep

    def abstract_representation(self, obj, size_limit, substitute_text):
        rep = self.get_image_representation(obj, size_limit)

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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:content_id>/suggest-tags/",
                self.admin_site.admin_view(self.suggest_tags_view),
                name="content-suggest-tags",
            ),
        ]
        return custom_urls + urls

    def suggest_tags_view(self, request, content_id):
        content_obj = self.get_object(request, content_id)
        if not content_obj:
            return redirect("admin:medialib_content_changelist")

        if request.method == "POST":
            selected_tags = request.POST.getlist("selected_tags")
            for tag_title in selected_tags:
                tag, _ = resolve_tag(tag_title, CategoryEnum.CONTENT)
                content_obj.tags.add(tag)
                implications = get_all_implications(tag)
                for i_tag in implications:
                    content_obj.tags.add(i_tag)

            self.message_user(request, f"Added {len(selected_tags)} tags.")
            return redirect("admin:medialib_content_change", content_id)

        try:
            cl1_image_representation = (
                content_obj.representation_set.filter(
                    repr_type=RepresentationTypeEnum.IMAGE,
                    compatibility_level=1,
                )
                .order_by("-width")
                .first()
            )
            with cl1_image_representation.filepath.open("rb") as f:
                response = requests.post(
                    "http://127.0.0.1:10877/tagging",
                    files={"image-file": f},
                    data={"threshold": 0.2},
                )
            tags_data = response.json()
        except Exception as e:
            self.message_user(
                request, f"AI Tagger error: {str(e)}", level=messages.ERROR
            )
            return redirect("admin:medialib_content_change", content_id)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "content_obj": content_obj,
            "representation": self.get_image_representation(content_obj, 512),
            "tags": tags_data,
            "title": f"Suggest tags for {content_obj.title}",
            "MEDIA_URL": MEDIA_URL,
        }
        return TemplateResponse(
            request, "admin/medialib/content/suggest_tags.djhtml", context
        )


class AlbumOrderInline(admin.TabularInline):
    model = ml_models.AlbumOrder
    extra = 0
    autocomplete_fields = ["content"]
    ordering = ("order",)


@admin.register(ml_models.Album)
class AlbumAdmin(admin.ModelAdmin):
    form = AlbumAdminForm
    inlines = [AlbumOrderInline]
    list_display = ("get_album_name", "get_creator_string", "album_set")
    exclude = ["creator_tags"]

    autocomplete_fields = ["album_set"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "album_set":
            kwargs["queryset"] = ml_models.Tag.objects.filter(
                category__in=[
                    ml_models.CategoryEnum.SET.value,
                    ml_models.CategoryEnum.COMIC.value,
                ]
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/sync/",
                self.admin_site.admin_view(self.sync_album_view),
                name="medialib_album_sync",
            ),
        ]
        return custom_urls + urls

    def sync_album_view(self, request, pk):
        album = self.get_object(request, pk)
        if album:
            count = album.sync_from_set()
            if count > 0:
                self.message_user(
                    request, f"Successful sync {count} elements."
                )
            else:
                self.message_user(
                    request,
                    "Nothing to sync (check album_set tag).",
                    messages.WARNING,
                )
        return redirect("admin:medialib_album_change", pk)

    change_form_template = "admin/medialib/album/change_form.html"
