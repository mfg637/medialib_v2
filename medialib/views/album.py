from django.views.generic import ListView, DetailView
from medialib.models import Album, AlbumOrder, Representation
from .content import get_items_per_page, ContentListItem
from .representation import generate_image_srcset
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Prefetch
from base.shared_enums.medialib_model import RepresentationTypeEnum


class AlbumListView(ListView):
    model = Album
    template_name = "medialib/album_list.djhtml"
    context_object_name = "albums"
    paginate_by = 20

    def get_queryset(self):
        repr_qs = (
            Representation.objects.filter(
                repr_type=RepresentationTypeEnum.IMAGE.value
            )
            .filter(Q(width__gte=192) | Q(height__gte=256))
            .order_by("width")
        )

        items_qs = (
            AlbumOrder.objects.order_by("order")
            .select_related("content")
            .prefetch_related(
                Prefetch("content__representation_set", queryset=repr_qs)
            )
        )

        queryset = Album.objects.all().prefetch_related(
            Prefetch("items", queryset=items_qs)
        )

        show_nsfw_raw = self.request.GET.get("nsfw", 0)
        try:
            show_nsfw = bool(int(show_nsfw_raw))
        except ValueError, TypeError:
            show_nsfw = False

        if not show_nsfw or not self.request.user.is_authenticated:
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

        if album.is_nsfw and not request.user.is_authenticated:
            raise PermissionDenied("Unable to show this album")

        queryset = album.contents.filter(album_item__album=album).order_by(
            "album_item__order"
        )

        items_per_page = get_items_per_page(request)
        paginator = Paginator(queryset, items_per_page)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        content_list = []
        for content in page_obj.object_list:
            srcset, base_src = generate_image_srcset(content, 256, 256)
            content_list.append(
                ContentListItem(
                    content.id,
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
