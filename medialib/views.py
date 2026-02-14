from django.shortcuts import render
from base.shared_enums.medialib_model import RepresentationTypeEnum
from medialib_v2.settings import MEDIA_URL
from .models import Content

# Create your views here.


def content_info(request, content_slug: str):
    content = Content.objects.get(slug=content_slug)
    repr_list = content.representation_set.filter(
        repr_type=RepresentationTypeEnum.IMAGE.value
    ).order_by("width")
    main_repr = None
    for current_repr in repr_list:
        if current_repr.check_side_size_limit(1024):
            main_repr = current_repr
    return render(
        request,
        "medialib/content_info.html",
        {
            "content": content,
            "MEDIA_URL": MEDIA_URL,
            "main_repr": main_repr,
        },
    )
