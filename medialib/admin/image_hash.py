from dataclasses import dataclass
from itertools import combinations
from django.contrib import admin, messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext
from django.urls import path
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from medialib_v2.settings import MEDIA_URL
from medialib.flow import ContentMergeFlow
from medialib import models as ml_models
from base.shared_enums.medialib_model import (
    RepresentationTypeEnum,
)


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
    readonly_fields = [
        "content",
        "aspect_ratio",
        "display_L_hash",
        "display_a_hash",
        "display_b_hash",
        "aspect_ratio",
    ]
    list_filter = ("alternate_version",)
    search_fields = ("content__title", "content__slug")

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
