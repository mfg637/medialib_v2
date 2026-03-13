from django.views.generic import ListView, DetailView
from medialib.models import Album
from .content import get_items_per_page, ContentListItem
from .representation import generate_image_srcset
from django.core.paginator import Paginator


class AlbumListView(ListView):
    model = Album
    template_name = "medialib/album_list.djhtml"
    context_object_name = "albums"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        show_nsfw_raw = self.request.GET.get("nsfw", 0)
        try:
            show_nsfw = bool(int(show_nsfw_raw))
        except ValueError, TypeError:
            show_nsfw = False

        if not show_nsfw:
            queryset = queryset.filter(is_nsfw=False)

        return queryset


class AlbumDetailView(DetailView):
    model = Album
    template_name = "medialib/album_detail.djhtml"
    context_object_name = "album"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.object
        request = self.request

        queryset = album.contents.all().order_by("albumorder__order")

        items_per_page = get_items_per_page(request)
        paginator = Paginator(queryset, items_per_page)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        content_list = []
        for content in page_obj.object_list:
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

        context["content_list"] = content_list
        context["page_obj"] = page_obj
        return context
