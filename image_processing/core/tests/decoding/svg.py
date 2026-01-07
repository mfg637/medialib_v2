from django.test import SimpleTestCase
from image_processing.config import samples_root_dir
from image_processing.core.decoders.common import open_image_as_vips_image
from image_processing.core import metrics


class TestSVG(SimpleTestCase):
    def test_lossless_rgb(self):
        svg_file_path = samples_root_dir.joinpath("test.svg")
        img = open_image_as_vips_image(svg_file_path)
        self.assertEqual(img.width, 32)
        self.assertEqual(img.height, 32)
        img_true = metrics.normalize_for_metrics(
            open_image_as_vips_image(samples_root_dir.joinpath("test.svg.png"))
        )
        img_test = metrics.normalize_for_metrics(img)
        result = metrics.calc_metrics(img_true, img_test)
        self.assertGreater(result["psnr"], 60.0)
