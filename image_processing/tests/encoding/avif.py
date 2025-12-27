from django.test import SimpleTestCase
from image_processing.decoders import open_image, AccessMode
from ..decoding import common as dec_com
from image_processing.metrics import normalize_for_metrics, calc_metrics

from image_processing.encoders import avif
from tempfile import NamedTemporaryFile


class TestAVIF(SimpleTestCase):
    def setUp(self):
        self.ref_rgb_image = open_image(
            dec_com.RGB_REFERENCE_IMAGE, access_mode=AccessMode.RANDOM
        ).copy_memory()
        self.ref_rgba_image = open_image(
            dec_com.RGB_REFERENCE_TRANSPARENT_IMAGE,
            access_mode=AccessMode.RANDOM,
        ).copy_memory()
        self.ref_gray_image = open_image(
            dec_com.GRAY_REFERENCE_IMAGE, access_mode=AccessMode.RANDOM
        ).copy_memory()
        return super().setUp()

    def test_rgb_y444_10bit(self):
        encoded_file = NamedTemporaryFile(
            suffix=".avif", delete=True, mode="bw"
        )
        avif.encode(
            self.ref_rgb_image,
            encoded_file.name,
            quality=90,
            subsample_mode=avif.SubsamplingMode.DISABLED,
        )
        decoded_image = open_image(encoded_file.name)
        image_true = normalize_for_metrics(self.ref_rgb_image)
        image_test = normalize_for_metrics(decoded_image)
        result = calc_metrics(image_true, image_test)
        self.assertAlmostEqual(result["psnr"], 47.5, delta=1.0)
        encoded_file.close()

    def test_rgba(self):
        encoded_file = NamedTemporaryFile(
            suffix=".avif", delete=True, mode="bw"
        )
        avif.encode(
            self.ref_rgba_image,
            encoded_file.name,
            quality=90,
            subsample_mode=avif.SubsamplingMode.DISABLED,
        )
        decoded_image = open_image(encoded_file.name)
        image_true = normalize_for_metrics(self.ref_rgba_image)
        image_test = normalize_for_metrics(decoded_image)
        result = calc_metrics(image_true, image_test)
        self.assertAlmostEqual(result["psnr"], 42.0, delta=1.0)
        encoded_file.close()

    def test_gray(self):
        encoded_file = NamedTemporaryFile(
            suffix=".avif", delete=True, mode="bw"
        )
        avif.encode(
            self.ref_gray_image,
            encoded_file.name,
            quality=90,
            subsample_mode=avif.SubsamplingMode.DISABLED,
        )
        decoded_image = open_image(encoded_file.name)
        image_true = normalize_for_metrics(self.ref_gray_image)
        image_test = normalize_for_metrics(decoded_image)
        result = calc_metrics(image_true, image_test)
        self.assertAlmostEqual(result["psnr"], 51.0, delta=1.0)
        encoded_file.close()

