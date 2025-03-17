from django.test import SimpleTestCase
from image_processing.decoders import open_image_and_save_tmp_png as open_image
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation
from . import common


class TestAVIF(SimpleTestCase):
    def test_lossy_rgb_y444_10bit(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_y444_10bit.avif"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 73.0)
        self.assertGreater(result["fsim"], 0.88)
        tmp_file.close()

    def test_lossy_rgb_y420_8bit(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_y420_8bit.avif"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 59.0)
        self.assertGreater(result["fsim"], 0.78)
        tmp_file.close()

    def test_lossy_rgba(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_transparent_yuv444_10bit.avif"))
        result = evaluation(
            str(common.RGB_REFERENCE_TRANSPARENT_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 75.0)
        self.assertGreater(result["fsim"], 0.93)
        tmp_file.close()

    def test_lossy_gray(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_gray_10bit.avif"))
        result = evaluation(
            str(common.GRAY_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 78.0)
        self.assertGreater(result["fsim"], 0.95)
        tmp_file.close()

    def test_lossy_gray_alpha(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_transparent_gray_10bit.avif"))
        result = evaluation(
            str(common.GRAY_REFERENCE_TRANSPARENT_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 83.0)
        self.assertGreater(result["fsim"], 0.95)
        tmp_file.close()