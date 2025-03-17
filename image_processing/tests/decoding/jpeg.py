from django.test import SimpleTestCase
from image_processing.decoders import open_image_and_save_tmp_png as open_image
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation
from . import common


class TestJPEG(SimpleTestCase):

    def test_rgb_yuv444(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_y444.jpg"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 61.0)
        self.assertGreater(result["fsim"], 0.73)
        tmp_file.close()
    
    def test_rgb_yuv444_arithmetic(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_y444_arithmetic.jpg"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 61.0)
        self.assertGreater(result["fsim"], 0.73)
        tmp_file.close()
    
    def test_rgb_yuv422(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_y422.jpg"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 59.0)
        self.assertGreater(result["fsim"], 0.71)
        tmp_file.close()

    def test_rgb_yuv420(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_rgb_y420.jpg"))
        result = evaluation(
            str(common.RGB_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 58.0)
        self.assertGreater(result["fsim"], 0.70)
        tmp_file.close()

    def test_gray(self):
        tmp_file = open_image(samples_root_dir.joinpath("lossy_gray_y444.jpg"))
        result = evaluation(
            str(common.GRAY_REFERENCE_IMAGE),
            tmp_file.name,
            ["psnr", "fsim"]
        )
        self.assertGreater(result["psnr"], 67.0)
        self.assertGreater(result["fsim"], 0.84)
        tmp_file.close()