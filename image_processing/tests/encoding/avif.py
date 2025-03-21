import pathlib
from django.test import SimpleTestCase
from image_processing.decoders import open_image
from image_processing.decoders import open_image_and_save_tmp_png
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation
from ..decoding import common as dec_com

from image_processing import encoders
from tempfile import NamedTemporaryFile


class TestAVIF(SimpleTestCase):
    def setUp(self):
        self.encoder = encoders.avif_encoder.AVIFEncoder
        self.ref_rgb_image = open_image(dec_com.RGB_REFERENCE_IMAGE)
        self.rgb_encoder = self.encoder(dec_com.RGB_REFERENCE_IMAGE, self.ref_rgb_image)
        self.ref_rgba_image = open_image(dec_com.RGB_REFERENCE_TRANSPARENT_IMAGE)
        self.rgba_encoder = self.encoder(dec_com.RGB_REFERENCE_TRANSPARENT_IMAGE, self.ref_rgba_image)
        self.ref_gray_image = open_image(dec_com.GRAY_REFERENCE_IMAGE)
        self.gray_encoder = self.encoder(dec_com.GRAY_REFERENCE_IMAGE, self.ref_gray_image)
        return super().setUp()
    
    def test_rgb_y444_10bit(self):
        self.rgb_encoder.bit_depth = 10
        avif_data = self.rgb_encoder.encode(95, force_subsampling=False)
        encoded_file = NamedTemporaryFile(suffix=".avif", delete=True, mode="bw")
        encoded_file.write(avif_data)
        decoded_file = open_image_and_save_tmp_png(pathlib.Path(encoded_file.name))
        result = evaluation(
            str(dec_com.RGB_REFERENCE_IMAGE),
            decoded_file.name,
            ["psnr",]
        )
        self.assertGreater(result["psnr"], 70.0)
        decoded_file.close()
        encoded_file.close()

    def test_rgb_y420_8bit(self):
        self.rgb_encoder.bit_depth = 8
        avif_data = self.rgb_encoder.encode(95, force_subsampling=True)
        encoded_file = NamedTemporaryFile(suffix=".avif", delete=True, mode="bw")
        encoded_file.write(avif_data)
        decoded_file = open_image_and_save_tmp_png(pathlib.Path(encoded_file.name))
        result = evaluation(
            str(dec_com.RGB_REFERENCE_IMAGE),
            decoded_file.name,
            ["psnr",]
        )
        self.assertGreater(result["psnr"], 59.0)
        decoded_file.close()
        encoded_file.close()
    
    def test_rgba(self):
        self.rgba_encoder.bit_depth = 10
        avif_data = self.rgba_encoder.encode(95, force_subsampling=False)
        encoded_file = NamedTemporaryFile(suffix=".avif", delete=True, mode="bw")
        encoded_file.write(avif_data)
        decoded_file = open_image_and_save_tmp_png(pathlib.Path(encoded_file.name))
        result = evaluation(
            str(dec_com.RGB_REFERENCE_TRANSPARENT_IMAGE),
            decoded_file.name,
            ["psnr",]
        )
        self.assertGreater(result["psnr"], 70.0)
        decoded_file.close()
        encoded_file.close()

    def test_gray(self):
        self.gray_encoder.bit_depth = 10
        avif_data = self.gray_encoder.encode(95, force_subsampling=False)
        encoded_file = NamedTemporaryFile(suffix=".avif", delete=True, mode="bw")
        encoded_file.write(avif_data)
        decoded_file = open_image_and_save_tmp_png(pathlib.Path(encoded_file.name))
        result = evaluation(
            str(dec_com.GRAY_REFERENCE_IMAGE),
            decoded_file.name,
            ["psnr",]
        )
        self.assertGreater(result["psnr"], 75.0)
        decoded_file.close()
        encoded_file.close()
    
    def tearDown(self):
        del self.rgb_encoder
        self.ref_rgb_image.close()
        del self.rgba_encoder
        self.ref_rgba_image.close()
        del self.gray_encoder
        self.ref_gray_image.close()
        return super().tearDown()