import requests
from typing import Optional
from django.apps import apps
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy
from django.urls import reverse, path
from django.template.response import TemplateResponse
from django.http import HttpRequest
from medialib_v2.settings import MEDIA_URL
from medialib import models as ml_models
from base.shared_enums.medialib_model import (
    CategoryEnum,
    RepresentationTypeEnum,
)
from base.view import format_file_size
from medialib.tags.tags_processing import resolve_tag, get_all_implications


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


class ContentOriginInline(admin.StackedInline):
    model = ml_models.ContentOrigin


class ContentRedirectInline(admin.StackedInline):
    model = ml_models.ContentRedirect

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[ml_models.Content]
    ) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[ml_models.Content]
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[ml_models.Content]
    ) -> bool:
        return False


class ProcessingResultInline(admin.StackedInline):
    model = apps.get_model("media_receiving", "TaskResult")
    extra = 0
    can_delete = False
    readonly_fields = [
        "task",
        "formatted_source",
        "formatted_result",
        "compression_ratio",
    ]
    fields = [
        "task",
        ("formatted_source", "formatted_result"),
        "compression_ratio",
    ]

    @admin.display(description=gettext_lazy("Source Size"))
    def formatted_source(self, obj):
        return format_file_size(obj.source_file_size)

    @admin.display(description=gettext_lazy("Result Size"))
    def formatted_result(self, obj):
        return format_file_size(obj.result_file_size)

    @admin.display(description=gettext_lazy("Compression / Change"))
    def compression_ratio(self, obj):
        if not obj.source_file_size:
            return "-"

        diff = obj.result_file_size - obj.source_file_size
        percent = (obj.result_file_size / obj.source_file_size) * 100

        if diff > 0:
            color = "red"
            status = gettext_lazy("Increased")
        elif diff < 0:
            color = "green"
            status = gettext_lazy("Reduced")
        else:
            color = "gray"
            status = gettext_lazy("No change")

        return mark_safe(
            f'<b style="color: {color};">{status} ({percent:.1f}%)</b> '
            f'<small style="color: #666;">[{"+" if diff > 0 else ""}{format_file_size(diff)}]</small>'
        )

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

    inlines = [
        RepresentationInline,
        ImageHashInline,
        ContentOriginInline,
        ContentRedirectInline,
        ProcessingResultInline,
    ]

    def formatted_hash(self, obj):
        if obj.source_hash:
            return obj.source_hash.tobytes().hex()
        return "-"

    formatted_hash.short_description = "Source Hash"

    @staticmethod
    def get_image_representation(obj, size_limit):
        repr_list = obj.representation_set.filter(
            repr_type=RepresentationTypeEnum.IMAGE.value
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

    def has_add_permission(self, request):
        return False

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

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        content = form.instance

        all_current_tags = content.tags.all()
        implied_tags_to_add = set()

        for tag in all_current_tags:
            implications = get_all_implications(tag)
            for implied_tag in implications:
                implied_tags_to_add.add(implied_tag)

        if implied_tags_to_add:
            content.tags.add(*implied_tags_to_add)
