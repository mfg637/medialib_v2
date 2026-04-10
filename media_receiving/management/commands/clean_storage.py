from pathlib import Path
from django.core.management.base import BaseCommand
from medialib_v2 import settings
from medialib.models import Representation
from media_receiving.models import Task


class Command(BaseCommand):
    help = "Junk file cleaner"

    def handle(self, *args, **options):
        queue_path = settings.MEDIALIB_QUEUE_ROOT
        active_task_files = set(
            Task.objects.values_list("uploaded_file", flat=True)
        )
        active_task_filenames = {Path(f).name for f in active_task_files if f}

        for file in queue_path.glob("*"):
            if file.is_file() and file.name not in active_task_filenames:
                self.stdout.write(
                    f"Removing orphan file from queue: {file.name}"
                )
                file.unlink()

        repr_root = settings.MEDIALIB_COLLECTION_ROOT
        db_repr_files = set(
            Representation.objects.values_list("filepath", flat=True)
        )

        for root, dirs, files in repr_root.walk():
            for filename in files:
                full_path = Path(root) / filename
                rel_path = str(full_path.relative_to(settings.MEDIALIB_ROOT))

                if rel_path not in db_repr_files:
                    self.stdout.write(
                        f"Removing orphan representation: {rel_path}"
                    )
                    full_path.unlink()

        self.stdout.write(self.style.SUCCESS("Cleaning is done!"))
