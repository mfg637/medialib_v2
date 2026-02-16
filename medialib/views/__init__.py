from django.http import HttpResponse
from django.shortcuts import render, redirect
from base.shared_enums.medialib_model import RepresentationTypeEnum
from medialib_v2.settings import MEDIA_URL
from medialib.models import Content
from . import representation

# Create your views here.


def content_info(request, content_slug: str) -> HttpResponse:
    content = Content.objects.get(slug=content_slug)
    has_image = content.representation_set.filter(
        repr_type=RepresentationTypeEnum.IMAGE.value
    ).exists()
    srcset_str = representation.generate_image_srcset(content, 1024, 1024)
    return render(
        request,
        "medialib/content_info.djhtml",
        {
            "content": content,
            "MEDIA_URL": MEDIA_URL,
            "srcset": srcset_str,
            "has_image": has_image,
        },
    )


def set_cl_level(request, level):
    request.session["clevel"] = level
    next_url = request.GET.get("next", "/")
    return redirect(next_url)


__all__ = ["content_info", "set_cl_level", "representation"]
