from . import views
from django.urls import path

urlpatterns = [
    path(
        "task/create/by_form",
        views.create_task_api,
        name="content-info",
    ),
    path(
        "task/create/by_file",
        views.create_task_from_local_file,
        name="content-representation",
    ),
]
