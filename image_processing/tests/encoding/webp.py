import pathlib
from django.test import SimpleTestCase
from image_processing.decoders import open_image
from image_processing.decoders import open_image_and_save_tmp_png
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation
from ..decoding import common as dec_com

from image_processing import encoders
from tempfile import NamedTemporaryFile


class Test_WEBP(SimpleTestCase):
    def setUp(self):
        self.encoder = encoders.webp_encoder.WEBPEncoder
        self.ref_rgb_image = open_image(dec_com.RGB_REFERENCE_IMAGE)
        self.lossy_encoding = self.encoder(dec_com.RGB_REFERENCE_IMAGE, self.ref_rgb_image)
        self.rgb_lossless_test_img = open_image(dec_com.RGB_LOSSLESS_IMAGE)
        self.lossless_encoding = self.encoder(dec_com.RGB_LOSSLESS_IMAGE, self.rgb_lossless_test_img)
        return super().setUp()
    
    def test_lossless_encode(self):
        webp_data = self.lossless_encoding.encode(100, lossless=True)
        encoded_file = NamedTemporaryFile(suffix=".webp", delete=True, mode="bw")
        encoded_file.write(webp_data)
        decoded_file = open_image_and_save_tmp_png(pathlib.Path(encoded_file.name))
        result = evaluation(
            str(dec_com.RGB_LOSSLESS_IMAGE),
            decoded_file.name,
            ["rmse", "psnr", "ssim", "fsim"]
        )
        self.assertEqual(result["rmse"], 0.0)
        self.assertEqual(result["psnr"], float("inf"))
        self.assertEqual(result["ssim"], 1.0)
        self.assertEqual(result["fsim"], 1.0)
        decoded_file.close()
        encoded_file.close()
    
    def test_lossy_encode(self):
        webp_data = self.lossy_encoding.encode(90, lossless=True)
        encoded_file = NamedTemporaryFile(suffix=".webp", delete=True, mode="bw")
        encoded_file.write(webp_data)
        decoded_file = open_image_and_save_tmp_png(pathlib.Path(encoded_file.name))
        result = evaluation(
            str(dec_com.RGB_REFERENCE_IMAGE),
            decoded_file.name,
            ["psnr",]
        )
        self.assertGreater(result["psnr"], 59.0)
        decoded_file.close()
        encoded_file.close()
    
    def tearDown(self):
        del self.lossy_encoding
        del self.lossless_encoding
        self.ref_rgb_image.close()
        self.rgb_lossless_test_img.close()
        return super().tearDown()
