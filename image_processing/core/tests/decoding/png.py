from django.test import SimpleTestCase
from image_processing.core.decoders import open_image_as_vips_image
from image_processing.config import samples_root_dir
import numpy as np


RGB24_TEST_DATA = np.array(
    [
        [0, 0, 0],
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255],
    ],
    dtype=np.uint8,
)

RGBA32_TEST_DATA = np.array(
    [
        [0, 0, 0, 0],
        [255, 0, 0, 255],
        [0, 255, 0, 255],
        [0, 0, 255, 255],
    ],
    dtype=np.uint8,
)

GRAYSCALE_TEST_DATA = np.array(
    [0, 64, 128, 255],
    dtype=np.uint8,
)

GRAYSCALE_TEST_DATA_RGB = np.stack(
    [GRAYSCALE_TEST_DATA] * 3,
    axis=1,
)

GRAYSCALE_ALPHA_TEST_DATA = np.array(
    [
        [0, 0],
        [64, 255],
        [128, 255],
        [255, 255],
    ],
    dtype=np.uint8,
)


GRAYSCALE_ALPHA_TEST_DATA_RGBA = np.column_stack(
    (
        np.stack([GRAYSCALE_ALPHA_TEST_DATA[:, 0]] * 3, axis=1),
        GRAYSCALE_ALPHA_TEST_DATA[:, 1],
    )
)


class TestPNG(SimpleTestCase):
    def decode(self, file_name: str) -> np.ndarray:
        img = open_image_as_vips_image(samples_root_dir / file_name)
        arr = img.numpy()
        return (
            arr.reshape(-1, arr.shape[-1])
            if arr.ndim == 3
            else arr.reshape(-1)
        )

    def test_rgb24(self):
        decoded_pixels = self.decode("rgb24.png")
        self.assertTrue(np.array_equal(decoded_pixels, RGB24_TEST_DATA))

    def test_indexed_color(self):
        decoded_pixels = self.decode("indexed_color.png")
        self.assertTrue(np.array_equal(decoded_pixels, RGB24_TEST_DATA))

    def test_rgba32(self):
        decoded_pixels = self.decode("rgba32.png")
        self.assertTrue(np.array_equal(decoded_pixels, RGBA32_TEST_DATA))

    def test_indexed_color_alpha(self):
        decoded_pixels = self.decode("indexed_color_alpha.png")
        self.assertTrue(np.array_equal(decoded_pixels, RGBA32_TEST_DATA))

    def test_grayscale(self):
        decoded_pixels = self.decode("grayscale.png")
        self.assertTrue(np.array_equal(decoded_pixels, GRAYSCALE_TEST_DATA))

    def test_grayscale_indexed(self):
        decoded_pixels = self.decode("indexed_grayscale.png")
        self.assertTrue(
            np.array_equal(decoded_pixels, GRAYSCALE_TEST_DATA_RGB)
        )

    def test_grayscale_alpha(self):
        decoded_pixels = self.decode("grayscale_alpha.png")
        self.assertTrue(
            np.array_equal(decoded_pixels, GRAYSCALE_ALPHA_TEST_DATA)
        )

    def test_grayscale_alpha_indexed(self):
        decoded_pixels = self.decode("indexed_grayscale_alpha.png")
        self.assertTrue(
            np.array_equal(decoded_pixels, GRAYSCALE_ALPHA_TEST_DATA_RGBA)
        )
