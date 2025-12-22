import pathlib
from image_processing import metrics
from image_processing.decoders.common import open_image_as_vips_image
from image_processing.tests.utils import debug_vips_image


def decoding_testing(
    image_true_path: pathlib.Path,
    image_test_path: pathlib.Path,
    debug: bool = False,
):
    image_true = metrics.normalize_for_metrics_srgb(
        open_image_as_vips_image(image_true_path)
    )
    image_test = metrics.normalize_for_metrics_srgb(
        open_image_as_vips_image(image_test_path)
    )
    if debug:
        debug_vips_image(image_true=image_true)
        debug_vips_image(image_test=image_test)

    result = metrics.calc_metrics(image_true, image_test)
    return result
