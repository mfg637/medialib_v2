import requests
from dataclasses import dataclass
from itertools import combinations
from django.contrib import admin, messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.urls import reverse, path
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from medialib_v2.settings import MEDIA_URL
from medialib.flow import ContentMergeFlow
from base.shared_knowledge.tags import generate_aliases
from medialib import models as ml_models
from base.shared_enums.medialib_model import (
    CategoryEnum,
    RepresentationTypeEnum,
)
from .forms import AlbumAdminForm
from .tags import smart_tag_search
from .tags.tags_processing import resolve_tag, get_all_implications


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
    ordering = ["category", "title"]

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


class ContentOriginInline(admin.StackedInline):
    model = ml_models.ContentOrigin


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

    inlines = [RepresentationInline, ImageHashInline, ContentOriginInline]

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
                    CategoryEnum.SET.value,
                    CategoryEnum.COMIC.value,
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


@dataclass(frozen=True)
class CompareElement:
    hash_obj: ml_models.ImageHash
    content: ml_models.Content
    best_repr: ml_models.Representation


@dataclass(frozen=True)
class ComparePair:
    first: CompareElement
    second: CompareElement
    is_size_equal: bool  # if False, heatmap generation prohibited
    same_origin: bool  # same origin but different origin ids may mean
    # that content on origin was replaced, or, what more imortant
    # that it may be an alternate version
    both_alternate_versions: bool  # if True, no decisions can be choosed


@admin.register(ml_models.ImageHash)
class ImageHashAdmin(admin.ModelAdmin):
    list_display = ("content", "aspect_ratio", "alternate_version")
    list_filter = ("alternate_version",)
    search_fields = ("content__title", "content__slug")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "duplicates/",
                self.admin_site.admin_view(self.duplicate_groups_view),
                name="imagehash-duplicates",
            ),
            path(
                "compare/",
                self.admin_site.admin_view(self.compare_view),
                name="imagehash-compare",
            ),
            path(
                "mark-as-alternate/",
                self.admin_site.admin_view(self.mark_as_alternate_view),
                name="imagehash-mark-alternate",
            ),
            path(
                "unmark-as-alternate/",
                self.admin_site.admin_view(self.unmark_as_alternate_view),
                name="imagehash-alternate-unmark",
            ),
            path(
                "merge/",
                self.admin_site.admin_view(self.merge_action_view),
                name="imagehash-merge-content",
            ),
        ]
        return custom_urls + urls

    def duplicate_groups_view(self, request):
        groups = ml_models.ImageHash.duplicates.get_duplicate_groups()

        context = {
            **self.admin_site.each_context(request),
            "title": "Duplicate suspicious",
            "groups": groups,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request, "admin/medialib/imagehash/duplicates.djhtml", context
        )

    def compare_view(self, request):
        ids_raw = request.GET.get("ids", "")
        if not ids_raw:
            return HttpResponseRedirect("../duplicates/")

        try:
            ids = [int(x) for x in ids_raw.split(",") if x.strip()]
        except ValueError:
            return HttpResponseBadRequest("Invalid IDs format")

        hashes = (
            ml_models.ImageHash.objects.filter(id__in=ids)
            .select_related("content")
            .prefetch_related("content__origin_set")
        )

        elements_map: dict[int, CompareElement] = {}
        for h in hashes:
            content = h.content
            best_repr = (
                content.representation_set.filter(
                    repr_type=RepresentationTypeEnum.IMAGE.value
                )
                .exclude(format="svg")
                .order_by("-width")
                .first()
            )
            elements_map[h.id] = CompareElement(
                hash_obj=h, content=content, best_repr=best_repr
            )

        compare_pairs: list[ComparePair] = []
        for id1, id2 in combinations(elements_map.keys(), 2):
            first, second = elements_map[id1], elements_map[id2]
            if first.best_repr and second.best_repr:
                size_equal = (
                    first.best_repr.width == second.best_repr.width
                    and first.best_repr.height == second.best_repr.height
                )
            else:
                raise Exception(
                    (
                        "Invalid content: "
                        "image content must have raster image representations"
                    )
                )
            first_origins = {
                origin.name for origin in first.content.origin_set.all()
            }
            second_origins = {
                origin.name for origin in second.content.origin_set.all()
            }
            same_origin = bool(first_origins & second_origins)
            both_alternate_versions = (
                first.hash_obj.alternate_version
                and second.hash_obj.alternate_version
            )
            compare_pairs.append(
                ComparePair(
                    first,
                    second,
                    size_equal,
                    same_origin,
                    both_alternate_versions,
                )
            )

        context = {
            **self.admin_site.each_context(request),
            "title": "Compare Media Group",
            "hashes": hashes,
            "hash_pairs": compare_pairs,
            "ids_str": ids_raw,
            "opts": self.model._meta,
            "MEDIA_URL": MEDIA_URL,
        }
        return TemplateResponse(
            request, "admin/medialib/imagehash/compare.djhtml", context
        )

    def mark_as_alternate_view(self, request):
        h1_id = request.GET.get("h1")
        h2_id = request.GET.get("h2")
        all_ids = request.GET.get("ids", "")

        if h1_id and h2_id:
            ml_models.ImageHash.objects.filter(id__in=[h1_id, h2_id]).update(
                alternate_version=True
            )
            messages.success(request, gettext("Marked as alternate versions."))

        return redirect(f"../compare/?ids={all_ids}")

    def unmark_as_alternate_view(self, request):
        h1_id = request.GET.get("h1")
        h2_id = request.GET.get("h2")
        all_ids = request.GET.get("ids", "")

        if h1_id and h2_id:
            ml_models.ImageHash.objects.filter(id__in=[h1_id, h2_id]).update(
                alternate_version=False
            )
            messages.success(request, gettext("Marked as review required."))

        return redirect(f"../compare/?ids={all_ids}")

    def merge_action_view(self, request):
        source_id = request.GET.get("source")
        target_id = request.GET.get("target")
        all_ids = request.GET.get("ids", "")

        source_content = get_object_or_404(ml_models.Content, id=source_id)
        target_content = get_object_or_404(ml_models.Content, id=target_id)

        merge_flow = ContentMergeFlow()
        try:
            merge_flow.execute(source_content, target_content)
            messages.success(
                request, gettext("Successfully merged content into target.")
            )
        except Exception as e:
            messages.error(request, f"Merge failed: {str(e)}")

        remaining_ids = [i for i in all_ids.split(",") if i != str(source_id)]
        new_ids_str = ",".join(remaining_ids)

        return redirect(f"../compare/?ids={new_ids_str}")
