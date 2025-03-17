from django.test import SimpleTestCase
from image_processing.decoders import open_image_and_save_tmp_png as open_image
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation
from . import common


class TestJPEG_XL(SimpleTestCase):
    def test_lossless_rgb(self):
        tmp_file = open_image(samples_root_dir.joinpath("test_lossless.jxl"))
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
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_d1.jxl"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 63.0)
        self.assertGreater(result["fsim"], 0.80)
        tmp_file.close()
