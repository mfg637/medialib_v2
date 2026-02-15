from django.urls import path
from . import views

urlpatterns = [
    path(
        "static/content/<slug:content_slug>/info",
        views.content_info,
        name="content-info",
    ),
    path("set-cl/<int:level>", views.set_cl_level, name="set-cl"),
]
