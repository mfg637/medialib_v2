from django.test import SimpleTestCase
from image_processing.config import samples_root_dir
from image_processing.tests.decoding.utils import decoding_testing
from . import common


class TestJPEG(SimpleTestCase):

    def test_rgb_yuv444(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_y444.jpg"),
        )
        self.assertAlmostEqual(result["psnr"], 35.5, delta=1.0)

    def test_rgb_yuv444_arithmetic(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_y444_arithmetic.jpg"),
        )
        self.assertAlmostEqual(result["psnr"], 35.5, delta=1.0)

    def test_rgb_yuv422(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_y422.jpg"),
        )
        self.assertAlmostEqual(result["psnr"], 32.0, delta=1.0)

    def test_rgb_yuv420(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_rgb_y420.jpg"),
        )
        self.assertAlmostEqual(result["psnr"], 31.0, delta=1.0)

    def test_gray(self):
        result = decoding_testing(
            common.GRAY_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_gray_y444.jpg"),
        )
        self.assertAlmostEqual(result["psnr"], 42.25, delta=1.0)
