import pathlib
from django.db import models
from .content import Content


class Attachments(models.Model):
    id: int
    content = models.ForeignKey(
        Content, on_delete=models.CASCADE, db_index=True
    )
    filepath = models.FilePathField(unique=True, null=False, db_index=True)
    title = models.CharField(max_length=64)
    format = models.CharField(max_length=12)

    def delete(self, *args, **kwargs):
        _filepath = pathlib.Path(str(self.filepath))
        _filepath.unlink(missing_ok=True)
        super().delete(*args, **kwargs)

    def __str__(self):
        return (
            f"Attachments content id: {self.content.id}, "
            f"filepath: {self.filepath}, "
            f"title={self.title}, "
            f"format: {self.format}"
        )
