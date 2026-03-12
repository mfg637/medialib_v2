from django import forms
from base.shared_enums.medialib_model import CategoryEnum
from .models import Album, Tag


class AlbumAdminForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = "__all__"

    def clean_album_set(self):
        album_set = self.cleaned_data.get("album_set")
        if album_set and album_set.category not in {
            CategoryEnum.SET,
            CategoryEnum.COMIC,
        }:
            raise forms.ValidationError(
                "album_set must have the 'set' or 'comic' category."
            )
        return album_set

    def clean_creator_tags(self):
        tags = self.cleaned_data.get("creator_tags")
        valid_categories = {
            CategoryEnum.CREATOR,
            CategoryEnum.ARTIST,
            CategoryEnum.PROMPTER,
        }
        for tag in tags:
            if tag.category not in valid_categories:
                raise forms.ValidationError(
                    f"Tag '{tag.title}' has invalid category. "
                    "Only creator/artist/prompter are allowed."
                )
        return tags
