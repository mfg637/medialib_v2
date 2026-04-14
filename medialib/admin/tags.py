from django.contrib import admin
from base.shared_knowledge.tags import generate_aliases
from medialib import models as ml_models

from medialib.tags import smart_tag_search


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
