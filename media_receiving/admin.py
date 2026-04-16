from django.db.models import Sum, Avg, Count, F
from django.contrib import admin
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.urls import path
from base.view import format_file_size
from .models import Task, AwaitingTaskMetadata, ExecutionError, TaskResult
from .forms import TaskUploadForm
from media_receiving.flow.processing import run_processing_selected_tasks


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


admin.site.register(ExecutionError)


@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_task_link",
        "get_content_link",
        "source_size",
        "result_size",
        "change_percent",
    ]
    list_filter = ["task__media_type", "task__status"]
    readonly_fields = [
        "task",
        "content",
        "source_file_size",
        "result_file_size",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def get_task_link(self, obj):
        return format_html(
            '<a href="../task/{0}/change/">Task #{0}</a>', obj.task.id
        )

    get_task_link.short_description = "Task"

    def get_content_link(self, obj):
        if obj.content:
            return format_html(
                '<a href="/admin/medialib/content/{0}/change/">Content #{0}</a>',
                obj.content.id,
            )
        return "-"

    get_content_link.short_description = "Content"

    def source_size(self, obj):
        return format_file_size(obj.source_file_size)

    def result_size(self, obj):
        return format_file_size(obj.result_file_size)

    def change_percent(self, obj):
        if not obj.source_file_size:
            return "0%"

        ratio = (obj.result_file_size / obj.source_file_size) * 100
        color = "var(--error-fg)" if ratio > 105 else "var(--success-fg)"
        if 95 <= ratio <= 105:
            color = "var(--body-fg)"

        formatted_ratio = f"{ratio:.1f}%"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            formatted_ratio,
        )

    change_percent.short_description = "Ratio"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "summary/",
                self.admin_site.admin_view(self.summary_view),
                name="processing-summary",
            ),
        ]
        return custom_urls + urls

    def summary_view(self, request):
        stats = (
            TaskResult.objects.values(
                mime=F("task__mime_type"), mtype=F("task__media_type")
            )
            .annotate(
                total_count=Count("id"),
                avg_source=Avg("source_file_size"),
                avg_result=Avg("result_file_size"),
                total_source=Sum("source_file_size"),
                total_result=Sum("result_file_size"),
            )
            .order_by("mtype", "mime")
        )

        overall_data = {
            "source": 0,
            "result": 0,
            "count": 0,
        }
        mtype_count = {"image": 0, "audio": 0, "video": 0}
        mtype_source = {"image": 0, "audio": 0, "video": 0}
        mtype_result = {"image": 0, "audio": 0, "video": 0}
        mime_summary_data = []
        for s in stats:
            ratio = (
                (s["total_result"] / s["total_source"] * 100)
                if s["total_source"]
                else 0
            )
            overall_data["source"] += s["total_source"]
            overall_data["result"] += s["total_result"]
            overall_data["count"] += s["total_count"]
            mtype_source[s["mtype"]] += s["total_source"]
            mtype_result[s["mtype"]] += s["total_result"]
            mtype_count[s["mtype"]] += s["total_count"]
            total_result = s["total_source"] - s["total_result"]
            total_result_str = format_file_size(abs(total_result))
            mime_summary_data.append(
                {
                    "mime": s["mime"] or "Unknown",
                    "type": s["mtype"],
                    "count": s["total_count"],
                    "avg_source": format_file_size(s["avg_source"]),
                    "avg_result": format_file_size(s["avg_result"]),
                    "total_saved": (
                        total_result_str
                        if total_result > 0
                        else f"-{total_result_str}"
                    ),
                    "ratio": f"{ratio:.1f}%",
                    "is_growth": ratio > 100,
                }
            )
        overall = {
            "source": format_file_size(overall_data["source"]),
            "result": format_file_size(overall_data["result"]),
            "count": overall_data["count"],
            "ratio": round(
                (
                    (overall_data["result"] / overall_data["source"] * 100)
                    if overall_data["source"]
                    else 0
                ),
                1,
            ),
            "avg_source": format_file_size(
                round(overall_data["source"] / overall_data["count"])
            ),
            "avg_result": format_file_size(
                round(overall_data["result"] / overall_data["count"])
            ),
            "total_saved": "None",
        }
        total_result_overall = overall_data["source"] - overall_data["result"]
        total_result_overall_str = format_file_size(abs(total_result))
        overall["total_saved"] = (
            total_result_overall_str
            if total_result_overall > 0
            else f"-{total_result_overall_str}"
        )
        mtype_stats = {"image": {}, "audio": {}, "video": {}}
        for mtype in ("image", "audio", "video"):
            mtype_stats[mtype] = {
                "source": format_file_size(mtype_source[mtype]),
                "result": format_file_size(mtype_result[mtype]),
                "count": mtype_count[mtype],
                "ratio": round(
                    (
                        (mtype_result[mtype] / mtype_source[mtype] * 100)
                        if mtype_source[mtype]
                        else 0
                    ),
                    1,
                ),
                "avg_source": format_file_size(
                    round(mtype_source[mtype] / mtype_count[mtype])
                    if mtype_count[mtype] > 0
                    else 0
                ),
                "avg_result": format_file_size(
                    round(mtype_result[mtype] / mtype_count[mtype])
                    if mtype_count[mtype] > 0
                    else 0
                ),
                "total_result": "",
            }
            total_result = mtype_source[mtype] - mtype_result[mtype]
            total_result_str = format_file_size(abs(total_result))
            mtype_stats[mtype]["total_result"] = (
                total_result_str
                if total_result > 0
                else f"-{total_result_str}"
            )

        context = {
            **self.admin_site.each_context(request),
            "title": "Processing Summary (Storage Impact)",
            "overall": overall,
            "mtype_stats": mtype_stats,
            "mime_stats": mime_summary_data,
        }
        return TemplateResponse(
            request, "admin/media_receiving/summary.djhtml", context
        )
