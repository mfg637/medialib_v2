from . import views
from django.urls import path

urlpatterns = [
    path(
        "task/create/by_form",
        views.create_task_api,
        name="api-task-create-form",
    ),
    path(
        "task/create/by_file",
        views.create_task_from_local_file,
        name="api-task-create-file",
    ),
    path("origin/info", views.origin_info, name="api-origin-info"),
]
