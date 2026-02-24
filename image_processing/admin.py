from django.contrib import admin
from .models import Task, AwaitingTaskMetadata
from .forms import TaskUploadForm
from image_processing.flow.processing import run_processing_selected_tasks


class MetadataInline(admin.StackedInline):
    model = AwaitingTaskMetadata
    can_delete = False
    verbose_name_plural = "Metadata of Task"
    exclude = ["tags"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskUploadForm
    inlines = [MetadataInline]

    list_display = ("id", "status", "created_at")
    list_filter = ("status",)
    actions = [run_processing_selected_tasks]
