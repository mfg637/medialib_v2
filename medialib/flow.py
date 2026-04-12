from django.db import transaction
from medialib.models import Content, ContentRedirect, AlbumOrder


class ContentMergeFlow:
    @transaction.atomic
    def execute(self, source_content: Content, target_content: Content):
        if source_content.id == target_content.id:
            return

        target_content.tags.add(*source_content.tags.all())

        for redirect in source_content.redirects.all():
            redirect.new_content = target_content
            redirect.save()

        for origin in source_content.origin_set.all():
            exists = target_content.origin_set.filter(
                name=origin.name, origin_id=origin.origin_id
            ).exists()
            if not exists:
                origin.content = target_content
                origin.alternate = True
                origin.save()
            else:
                origin.delete()

        for attachment in source_content.attachments_set.all():
            attachment.content = target_content
            attachment.save()

        for collection in source_content.in_collection.all():
            collection.items.add(target_content)

        for album_order in source_content.album_item.all():
            album = album_order.album
            already_in_album = AlbumOrder.objects.filter(
                album=album, content=target_content
            ).exists()

            if not already_in_album:
                album_order.content = target_content
                album_order.save()
            else:
                album_order.delete()

        ContentRedirect.objects.create(
            old_slug=source_content.slug,
            new_content=target_content,
            created_at=source_content.addition_date,
            source_hash=source_content.source_hash,
        )

        for repr_obj in source_content.representation_set.all():
            if repr_obj.filepath:
                repr_obj.filepath.delete(save=False)

        source_content.delete()
