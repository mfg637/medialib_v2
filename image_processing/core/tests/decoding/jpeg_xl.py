from django.test import SimpleTestCase
from image_processing.config import samples_root_dir
from image_processing.core.tests.decoding.utils import decoding_testing
from . import common


class TestJPEG_XL(SimpleTestCase):
    def test_lossless_rgb(self):
        result = decoding_testing(
            common.RGB_LOSSLESS_IMAGE,
            samples_root_dir.joinpath("test_lossless.jxl"),
        )
        self.assertEqual(result["rmse"], 0.0)
        self.assertEqual(result["psnr"], float("inf"))

    def test_lossy_rgb(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_d1.jxl"),
        )
        self.assertAlmostEqual(result["psnr"], 38.5, delta=1.0)
