from django.test import SimpleTestCase
from image_processing.config import samples_root_dir
from image_processing.tests.decoding.utils import decoding_testing
from . import common


class TestWEBP(SimpleTestCase):
    def test_lossless_rgb(self):
        result = decoding_testing(
            common.RGB_LOSSLESS_IMAGE,
            samples_root_dir.joinpath("test_lossless.webp"),
        )
        self.assertEqual(result["rmse"], 0.0)
        self.assertEqual(result["psnr"], float("inf"))

    def test_lossy_rgb(self):
        result = decoding_testing(
            common.RGB_REFERENCE_IMAGE, samples_root_dir.joinpath("lossy.webp")
        )

        self.assertAlmostEqual(result["psnr"], 35.5, delta=1.5)

    def test_lossy_rgba(self):
        result = decoding_testing(
            common.RGB_REFERENCE_TRANSPARENT_IMAGE,
            samples_root_dir.joinpath("lossy_transparent.webp"),
        )
        self.assertAlmostEqual(result["psnr"], 39.5, delta=1.5)
        self.assertAlmostEqual(result["rmse"], 3, delta=0.5)

    def test_lossy_gray(self):
        result = decoding_testing(
            common.GRAY_REFERENCE_IMAGE,
            samples_root_dir.joinpath("lossy_gray.webp"),
        )

        self.assertAlmostEqual(result["psnr"], 49.5, delta=1.5)

    def test_lossy_gray_alpha(self):
        result = decoding_testing(
            common.GRAY_REFERENCE_TRANSPARENT_IMAGE,
            samples_root_dir.joinpath("lossy_transparent_gray.webp"),
        )

        self.assertAlmostEqual(result["psnr"], 47.5, delta=1.5)
