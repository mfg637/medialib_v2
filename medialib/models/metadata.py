from django.db import models
from django.core.exceptions import ValidationError
from base.shared_enums.medialib_model import CategoryEnum
from .base import (
    TAG_NAME_LENGTH_LIMIT,
    TAG_ALIAS_LENGRG_LIMIT,
)


class Tag(models.Model):
    id: int
    implications_target = models.Manager["TagImplications"]
    implications_implicated = models.Manager["TagImplications"]
    alias_set = models.Manager["TagAlias"]
    title = models.CharField(
        max_length=TAG_NAME_LENGTH_LIMIT, null=False, blank=False
    )
    CATEGORY_CHOICES = [
        (CategoryEnum.CREATOR, "Content creator"),
        (CategoryEnum.ARTIST, "Artist"),
        (CategoryEnum.PROMPTER, "Prompter"),
        (CategoryEnum.AI, "AI related metadata"),
        (CategoryEnum.SET, "Unordered set"),
        (CategoryEnum.COMIC, "Comic pages set"),
        (CategoryEnum.COPYRIGHT, "Copyright"),
        (CategoryEnum.RATING, "Rating"),
        (CategoryEnum.SPECIES, "Species"),
        (CategoryEnum.CHARACTER, "Character name"),
        (CategoryEnum.CHARACTER_GROUP, "Group of characters"),
        (CategoryEnum.GENDER, "Gender"),
        (CategoryEnum.LORE, "Lore metadata"),
        (CategoryEnum.META, "Metadata"),
        (CategoryEnum.ERROR, "Error"),
        (CategoryEnum.STYLE, "Style description"),
        (CategoryEnum.CONTENT, "Content description"),
    ]
    category = models.CharField(
        choices=CATEGORY_CHOICES,
        db_index=True,
        default=CategoryEnum.CONTENT.value,
    )
    implications = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="TagImplications",
        through_fields=("target", "implicate"),
        related_name="is_implied_by",
    )

    def get_category(self: Tag) -> CategoryEnum:
        return CategoryEnum(self.category)

    def __str__(self):
        return f"Tag: {self.title} ({self.category})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "category"],
                name="unique_tag_title_category",
            )
        ]


class TagImplications(models.Model):
    id: int
    target_id: int
    implicate_id: int
    target = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="implications_target",
    )
    implicate = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="implications_implicated"
    )

    def clean(self):
        if self.target_id == self.implicate_id:
            raise ValidationError("Tag can't implicate itself")
        return super().clean()

    class Meta:
        verbose_name = "implication of tag"
        verbose_name_plural = "implications of tag"
        constraints = [
            models.UniqueConstraint(
                fields=["target", "implicate"],
                name="unique_tag_to_implication",
            )
        ]

    def __str__(self) -> str:
        return (
            "TagImplications target: "
            f"{self.target}, implicates: {self.implicate}"
        )


class TagAlias(models.Model):
    id: int
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, db_index=True, related_name="alias_set"
    )
    title = models.CharField(
        unique=True,
        null=False,
        blank=False,
        db_index=True,
        max_length=TAG_ALIAS_LENGRG_LIMIT,
    )

    class Meta:
        verbose_name = "alias of tag"
        verbose_name_plural = "aliases of tag"

    def __str__(self) -> str:
        return f"TagAlias: {self.title}, tag id: {self.tag.id}"
