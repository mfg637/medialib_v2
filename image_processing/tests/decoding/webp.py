from django.test import SimpleTestCase
from image_processing.decoders import open_image_and_save_tmp_png as open_image
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation
from . import common


class TestWEBP(SimpleTestCase):
    def test_lossless_rgb(self):
        tmp_file = open_image(samples_root_dir.joinpath("test_lossless.webp"))
        result = evaluation(
            str(common.RGB_LOSSLESS_IMAGE),
            tmp_file.name,
            ["rmse", "psnr", "ssim", "fsim"]
        )
        self.assertEqual(result["rmse"], 0.0)
        self.assertEqual(result["psnr"], float("inf"))
        self.assertEqual(result["ssim"], 1.0)
        self.assertEqual(result["fsim"], 1.0)
        tmp_file.close()

    def test_lossy_rgb(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy.webp"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 59.0)
        self.assertGreater(result["fsim"], 0.76)
        tmp_file.close()

    def test_lossy_rgba(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_transparent.webp"))
        result = evaluation(
            str(common.RGB_REFERENCE_TRANSPARENT_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 49.0)
        self.assertGreater(result["fsim"], 0.77)
        tmp_file.close()

    def test_lossy_gray(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_gray.webp"))
        result = evaluation(
            str(common.GRAY_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 73.0)
        self.assertGreater(result["fsim"], 0.91)
        tmp_file.close()

    def test_lossy_gray_alpha(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_transparent_gray.webp"))
        result = evaluation(
            str(common.GRAY_REFERENCE_TRANSPARENT_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 62.0)
        self.assertGreater(result["fsim"], 0.82)
        tmp_file.close()
