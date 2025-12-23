from django.test import SimpleTestCase
from image_processing.config import samples_root_dir
from image_processing.tests.decoding.utils import decoding_testing
from . import common


class TestAVIF(SimpleTestCase):
    def test_lossy_rgb_y444_10bit(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_y444_10bit.avif"),
        )
        self.assertAlmostEqual(result["psnr"], 48.0, delta=1.0)

    def test_lossy_rgb_y420_8bit(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_y420_8bit.avif"),
        )
        self.assertAlmostEqual(result["psnr"], 32.5, delta=1.0)

    def test_lossy_rgba(self):
        result = decoding_testing(
            common.RGB_REFERENCE_TRANSPARENT_IMAGE,
            samples_root_dir.joinpath("lossy_transparent_yuv444_10bit.avif"),
        )
        self.assertAlmostEqual(result["psnr"], 42.0, delta=1.0)

    def test_lossy_gray(self):
        result = decoding_testing(
            common.GRAY_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_gray_10bit.avif"),
        )
        self.assertAlmostEqual(result["psnr"], 55.5, delta=1.0)

    def test_lossy_gray_alpha(self):
        result = decoding_testing(
            common.GRAY_REFERENCE_TRANSPARENT_IMAGE,
            samples_root_dir.joinpath("lossy_transparent_gray_10bit.avif"),
        )
        self.assertAlmostEqual(result["psnr"], 42.75, delta=1.0)
