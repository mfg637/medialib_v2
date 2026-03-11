from django.urls import path
from . import views

urlpatterns = [
    path(
        "static/content/<slug:content_slug>/info",
        views.content.content_info,
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
        "collections/<int:pk>/add/",
        views.collection.collection_add_item,
        name="collection-add-item",
    ),
]
