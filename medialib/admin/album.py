from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from medialib import models as ml_models
from base.shared_enums.medialib_model import (
    CategoryEnum,
)
from medialib.forms import AlbumAdminForm


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
