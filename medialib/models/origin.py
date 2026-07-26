from django.db import models
from base.shared_knowledge import origin
from .content import Content


class ContentOrigin(models.Model):
    id: int
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        db_index=True,
        related_name="origin_set",
    )
    name = models.CharField(max_length=32)
    origin_id = models.CharField(
        "ID on origin", max_length=255, blank=True, default=""
    )
    alternate = models.BooleanField(default=False)

    def get_url_if_possible(self) -> str:
        if self.origin_id is None:
            return ""
        origin_type = origin.get_origin_type(self.name)
        if origin_type is None:
            return ""
        origin_class: origin.AbstractOriginType = origin_type()
        return origin_class.generate_url(self.origin_id)

    def get_origin_info(self) -> origin.AbstractOriginType:
        origin_id = self.origin_id if self.origin_id else None
        return origin.ORIGIN_TYPE[self.name](origin_id, self.alternate)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "origin_id"],
                name="unique_origin_source_id",
                condition=~models.Q(origin_id=""),
            )
        ]
        indexes = [models.Index(fields=["name", "origin_id"])]
