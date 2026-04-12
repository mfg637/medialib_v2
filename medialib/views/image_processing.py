from django.http import HttpResponse, HttpResponseBadRequest
from image_processing.core.transforms import diff
from image_processing.core.libvips.definitions import Image as VipsImage
from medialib.models import Representation


def compare_representations_bin_view(request):
    id1 = request.GET.get("repr_id1")
    id2 = request.GET.get("repr_id2")

    if not id1 or not id2:
        return HttpResponseBadRequest("Missing representation IDs")

    repr1 = Representation.objects.filter(id=id1).first()
    repr2 = Representation.objects.filter(id=id2).first()

    if not repr1 or not repr2:
        return HttpResponseBadRequest("Representations not found")

    img1 = VipsImage.new_from_file(repr1.filepath.path)
    img2 = VipsImage.new_from_file(repr2.filepath.path)

    try:
        heatmap_array = diff.generate_diff_heatmap(img1, img2)

        raw_bytes = heatmap_array.astype("<u2").tobytes()

        response = HttpResponse(
            raw_bytes, content_type="application/octet-stream"
        )
        response["X-Width"] = heatmap_array.shape[1]
        response["X-Height"] = heatmap_array.shape[0]
        return response

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
