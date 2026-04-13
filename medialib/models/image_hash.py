import dataclasses
from collections import defaultdict
from django.db import models
from django.core.exceptions import ValidationError
from .content import Content


@dataclasses.dataclass(frozen=True)
class ImageHashGroupItem:
    imagehash_id: int
    content: Content
    aspect_ratio: float
    alternate_version: bool

    def __str__(self):
        return (
            f"content id = {self.content.id}, "
            f"aspect_ratio = {self.aspect_ratio}, "
            f"alternate_version = {self.alternate_version}"
        )

    def __repr__(self) -> str:
        return (
            "ImageHashGroupItem (\n"
            f"\tcontent={self.content}\n"
            f"\taspect_ratio={self.aspect_ratio}\n"
            f"\talternate_version={self.alternate_version}\n"
            ")"
        )


@dataclasses.dataclass(frozen=True)
class ImageHashGroup:
    short_hash_hex: str
    L_hash: bytes
    a_hash: bytes
    b_hash: bytes
    items: list[ImageHashGroupItem]
    count: int

    def __str__(self) -> str:
        return f"ImageHashGroup {self.short_hash_hex} ({self.count} items)"

    def __repr__(self) -> str:
        result_str = self.__str__() + "\n"
        for item in self.items:
            result_str += f"\t{item.__str__()}\n"
        return result_str


class ImageHashManager(models.Manager):
    def get_duplicate_groups(self) -> list[ImageHashGroup]:
        duplicate_hashes = (
            self.values("L_hash", "a_hash", "b_hash", "search_similar")
            .annotate(num_duplicates=models.Count("id"))
            .filter(num_duplicates__gt=1)
        )

        if not duplicate_hashes:
            return []

        all_items_qs = self.select_related("content").filter(
            L_hash__in=[h["L_hash"] for h in duplicate_hashes],
            search_similar__in=[h["search_similar"] for h in duplicate_hashes],
        )

        temp_map = defaultdict(list)
        for obj in all_items_qs:
            key = (obj.L_hash, obj.a_hash, obj.b_hash)
            temp_map[key].append(
                ImageHashGroupItem(
                    imagehash_id=obj.pk,
                    content=obj.content,
                    aspect_ratio=obj.aspect_ratio,
                    alternate_version=obj.alternate_version,
                )
            )

        groups = []
        for h in duplicate_hashes:
            key = (h["L_hash"], h["a_hash"], h["b_hash"])
            group_items = temp_map.get(key, [])

            if any(not item.alternate_version for item in group_items):
                groups.append(
                    ImageHashGroup(
                        short_hash_hex=h["search_similar"].hex(),
                        L_hash=h["L_hash"].tobytes(),
                        a_hash=h["a_hash"].tobytes(),
                        b_hash=h["b_hash"].tobytes(),
                        items=group_items,
                        count=len(group_items),
                    )
                )
        return groups


class ImageHash(models.Model):
    id: int
    content = models.OneToOneField(
        Content,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="imagehash",
    )
    aspect_ratio = models.FloatField("Aspect Ratio")
    L_hash = models.BinaryField(
        "Lightness component hash", max_length=32, db_index=True
    )
    a_hash = models.BinaryField(
        "a* component hash", max_length=8, db_index=True
    )
    b_hash = models.BinaryField(
        "b* component hash", max_length=8, db_index=True
    )
    search_similar = models.BinaryField(
        max_length=8, db_index=True, null=False
    )
    far_similarity = models.BinaryField(
        max_length=4, db_index=True, null=False
    )
    alternate_version = models.BooleanField(default=False, db_index=True)
    objects = models.Manager()
    duplicates = ImageHashManager()

    class Meta:
        verbose_name = "Image Hash"
        verbose_name_plural = "Image Hashes"
        indexes = [
            models.Index(fields=["L_hash", "a_hash", "b_hash"]),
        ]

    def save(self, *args, **kwargs):
        if not (self.L_hash and self.a_hash and self.b_hash):
            raise ValidationError(
                f"ImageHash for content {self.content.id} cannot be saved with empty hash fields. "
                f"L: {len(self.L_hash)}b, a: {len(self.a_hash)}b, b: {len(self.b_hash)}b"
            )

        self.search_similar = (
            bytes(self.L_hash)[:4]
            + bytes(self.a_hash)[:2]
            + bytes(self.b_hash)[:2]
        )
        self.far_similarity = (
            bytes(self.L_hash)[:2]
            + bytes(self.a_hash)[:1]
            + bytes(self.b_hash)[:1]
        )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"ImageHash content id {self.content.id}, "
            f"aspect ratio: {self.aspect_ratio}, "
            f"L hash: {self.L_hash.hex()}, "
            f"a hash: {self.a_hash.hex()}, "
            f"b hash: {self.b_hash.hex()}, "
            f"alternate version: {self.alternate_version}"
        )
