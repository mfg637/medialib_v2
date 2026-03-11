from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from medialib.models import Collection, Content
from django.core.paginator import Paginator
from .content import get_items_per_page, ContentListItem
from .representation import generate_image_srcset
from medialib_v2.settings import MEDIA_URL


@login_required
def collection_list(request):
    collections = Collection.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    return render(
        request,
        "medialib/collection_list.djhtml",
        {"collections": collections},
    )


@login_required
def collection_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            Collection.objects.get_or_create(user=request.user, title=title)
    return redirect("collection-list")


@login_required
def collection_detail(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    items_per_page = get_items_per_page(request)

    paginator = Paginator(collection.items.all(), items_per_page)
    page_number = int(request.GET.get("page", 1))
    page_obj = paginator.get_page(page_number)

    _content_list_raw = page_obj.object_list
    content_list: list[ContentListItem] = []
    for content in _content_list_raw:
        srcset, base_src = generate_image_srcset(content, 256, 256)
        content_list.append(
            ContentListItem(
                content.slug,
                base_src,
                content.content_type,
                content.title,
                srcset,
            )
        )
    return render(
        request,
        "medialib/collection_detail.djhtml",
        {
            "collection": collection,
            "content_list": content_list,
            "page_obj": page_obj,
            "MEDIA_URL": MEDIA_URL,
        },
    )


@login_required
def collection_add_item(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    if request.method == "POST":
        content_id = request.POST.get("content_id")
        try:
            content_item = Content.objects.get(id=content_id)
            collection.items.add(content_item)
        except Content.DoesNotExist, ValueError:
            pass
    return redirect("collection-detail", pk=pk)
