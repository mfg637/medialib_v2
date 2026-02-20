from django.core.management.base import BaseCommand
from django.db import transaction
from medialib.models import Tag, TagImplications
from base.shared_enums.medialib_model import CategoryEnum
from image_processing.services.tags_processing import resolve_tag


class Command(BaseCommand):
    help = (
        "generates CREATOR-tags and implications "
        "for existing ARTIST and PROMPTER tags"
    )

    def handle(self, *args, **options):
        source_categories = [CategoryEnum.ARTIST, CategoryEnum.PROMPTER]
        tags_to_process = Tag.objects.filter(category__in=source_categories)

        total = tags_to_process.count()
        self.stdout.write(f"Found {total} tags for processing.")

        created_creators = 0
        created_implications = 0

        with transaction.atomic():
            for index, tag in enumerate(tags_to_process, 1):
                import sys

                sys.stdout.write(
                    f"\rProcessing: {index}/{total} [{tag.title[:20]}]"
                )
                sys.stdout.flush()

                creator_tag, created = resolve_tag(
                    tag.title, CategoryEnum.CREATOR
                )

                if created:
                    created_creators += 1

                _, imp_created = TagImplications.objects.get_or_create(
                    target=tag, implicate=creator_tag
                )

                if imp_created:
                    created_implications += 1

        self.stdout.write("\n")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created new Creator-tags: {created_creators}, "
                f"new implications: {created_implications}"
            )
        )
