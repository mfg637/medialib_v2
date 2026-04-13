from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from base.shared_enums.medialib_model import (
    CategoryEnum,
)
from .content import Content
from .metadata import Tag


class Album(models.Model):
    id: int
    album_item = models.Manager["AlbumOrder"]
    album_set = models.ForeignKey(
        Tag,
        on_delete=models.PROTECT,
        related_name="album_set",
        null=True,
        blank=True,
    )
    creator_tags = models.ManyToManyField(
        Tag, related_name="creator_albums", blank=True
    )
    album_name = models.TextField(blank=True, default="")
    contents = models.ManyToManyField(
        Content,
        through="AlbumOrder",
        through_fields=("album", "content"),
        related_name="albums",
    )
    is_nsfw = models.BooleanField(default=False)

    def clean(self):
        if self.album_set is not None and self.album_set.category not in {
            CategoryEnum.SET,
            CategoryEnum.COMIC,
        }:
            raise ValidationError("album_set must have the 'set' category.")
        if self.pk:
            valid_categories = {
                CategoryEnum.CREATOR,
                CategoryEnum.ARTIST,
                CategoryEnum.PROMPTER,
            }

            invalid_creators = self.creator_tags.exclude(
                category__in=valid_categories
            )

            if invalid_creators.exists():
                raise ValidationError(
                    (
                        "All creator_tags must belong "
                        "to one on this categories: "
                        "creator/artist/prompter."
                    )
                )
        super().clean()

    def sync_from_set(self):
        if not self.album_set:
            return 0

        contents = Content.objects.filter(
            tags=self.album_set
        ).prefetch_related(
            models.Prefetch(
                "tags",
                queryset=Tag.objects.filter(
                    category=CategoryEnum.CREATOR.value
                ),
                to_attr="prefetched_creators",  # creates list[Tag]
            ),
            "origin_set",
        )

        def get_sort_key(content_item):
            try:
                origins = [
                    o for o in content_item.origin_set.all() if not o.alternate
                ]
                origin_obj = (
                    origins[0]
                    if origins
                    else content_item.origin_set.all().first()
                )

                if origin_obj and origin_obj.origin_id:
                    val = int(origin_obj.origin_id)
                else:
                    val = 2**64 - 1

                return (val, content_item.id)
            except ValueError, TypeError, AttributeError:
                return (2**64 - 1, content_item.id)

        sorted_contents = sorted(contents, key=get_sort_key)

        creators_unique = set()
        for content in contents:
            for (
                creator
            ) in (
                content.prefetched_creators  # pyright: ignore[reportAttributeAccessIssue]
            ):
                creators_unique.add(creator)

        with transaction.atomic():
            if creators_unique:
                self.creator_tags.set(list(creators_unique))

            AlbumOrder.objects.filter(album=self).delete()

            new_orders = [
                AlbumOrder(album=self, content=item, order=idx + 1)
                for idx, item in enumerate(sorted_contents)
            ]
            AlbumOrder.objects.bulk_create(new_orders)

        return len(new_orders)

    def get_album_name(self) -> str:
        if self.album_name:
            return self.album_name
        elif self.album_set is not None:
            return self.album_set.title
        else:
            return "untitled"

    def get_creator_string(self) -> str:
        creator_titles = list(
            self.creator_tags.values_list("title", flat=True)
        )

        if not creator_titles:
            return "Unknown Creators"

        return " and ".join(creator_titles)

    def __str__(self):
        return f"{self.get_album_name()} by {self.get_creator_string()}"


class AlbumOrder(models.Model):
    id: int
    album = models.ForeignKey(
        Album, on_delete=models.CASCADE, db_index=True, related_name="items"
    )
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="album_item",
    )
    order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "album",
                    "content",
                ],
                name="unique_content_to_album",
            ),
            models.UniqueConstraint(
                fields=["album", "order"],
                name="unique_album_order_position",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"AlbumOrder id: {self.album.id}, "
            f"content id: {self.content.id}, "
            f"order: {self.order}"
        )


class Collection(models.Model):
    id: int
    title = models.CharField(max_length=255, blank=False, null=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections",
    )
    items = models.ManyToManyField(
        "Content", related_name="in_collection", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_nsfw = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "title"],
                name="unique_collection",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "title"], name="collection_user_title_idx"
            )
        ]
