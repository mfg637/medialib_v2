from django.test import SimpleTestCase
from image_processing.core.decoders import open_image, AccessMode
from ..decoding import common as dec_com
from image_processing.core.metrics import (
    normalize_for_metrics,
    calc_metrics,
    normalize_for_metrics_srgb,
)
from image_processing.core.encoders import webp
from tempfile import NamedTemporaryFile


class Test_WEBP(SimpleTestCase):
    def setUp(self):
        self.ref_rgb_image = open_image(
            dec_com.RGB_REFERENCE_IMAGE, access_mode=AccessMode.RANDOM
        ).copy_memory()
        self.rgb_lossless_test_img = open_image(
            dec_com.RGB_LOSSLESS_IMAGE, access_mode=AccessMode.RANDOM
        ).copy_memory()
        return super().setUp()

    def test_lossless_encode(self):
        encoded_file = NamedTemporaryFile(
            suffix=".webp", delete=True, mode="bw"
        )
        webp.encode(self.ref_rgb_image, encoded_file.name, lossless=True)
        true_image = normalize_for_metrics_srgb(self.ref_rgb_image)
        test_image = normalize_for_metrics_srgb(open_image(encoded_file.name))
        result = calc_metrics(true_image, test_image)
        self.assertEqual(result["rmse"], 0.0)
        self.assertEqual(result["psnr"], float("inf"))
        encoded_file.close()

    def test_lossy_encode(self):
        encoded_file = NamedTemporaryFile(
            suffix=".webp", delete=True, mode="bw"
        )
        webp.encode(self.ref_rgb_image, encoded_file.name, quality=95)
        true_image = normalize_for_metrics(self.ref_rgb_image)
        test_image = normalize_for_metrics(open_image(encoded_file.name))
        result = calc_metrics(true_image, test_image)
        self.assertAlmostEqual(result["rmse"], 0.025, delta=0.005)
        self.assertAlmostEqual(result["psnr"], 32.0, delta=1.0)
        encoded_file.close()
