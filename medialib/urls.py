from django.urls import path
from . import views

urlpatterns = [
    path(
        "static/content/mlid<int:content_id>/info",
        views.content.content_info_by_id,
        name="content-info",
    ),
    path(
        "static/content/<slug:content_slug>/info",
        views.content.content_info_by_slug,
        name="content-info",
    ),
    path(
        "dynamic/content/<slug:content_slug>/representation",
        views.representation.get_representation,
        name="content-representation",
    ),
    path(
        "dynamic/content/list", views.content.content_list, name="content-list"
    ),
    path("tag/id<int:tag_id>", views.tag_info, name="tag-info"),
    path("set-cl/<int:level>", views.set_cl_level, name="set-cl"),
    path(
        "collections/",
        views.collection.collection_list,
        name="collection-list",
    ),
    path(
        "collections/<int:pk>/",
        views.collection.collection_detail,
        name="collection-detail",
    ),
    path(
        "collections/create/",
        views.collection.collection_create,
        name="collection-create",
    ),
    path(
        "collection/add-item",
        views.collection.collection_add_item_direct,
        name="collection-add-item-direct",
    ),
    path(
        "collections/<int:pk>/add/",
        views.collection.collection_add_item,
        name="collection-add-item",
    ),
    path(
        "collections/<int:pk>/toggle-nsfw/",
        views.collection.collection_toggle_nsfw,
        name="collection-toggle-nsfw",
    ),
    path(
        "albums/list",
        views.album.AlbumListView.as_view(),
        name="album-list",
    ),
    path(
        "albums/<int:pk>/view",
        views.album.AlbumDetailView.as_view(),
        name="album-detail",
    ),
]
