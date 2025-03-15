from django.test import SimpleTestCase
from image_processing import open_image
from PIL.Image import Image
from image_processing.config import samples_root_dir


RGB24_TEST_DATA = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
RGBA32_TEST_DATA = [(0, 0, 0, 0), (255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]
GRAYSCALE_TEST_DATA = [0, 64, 128, 255]
GRAYSCALE_ALPHA_TEST_DATA = [(0, 0), (64, 255), (128, 255), (255, 255)]


class TestPNG(SimpleTestCase):
    """
    This test intended to check that Pillow library correctly reads PNG files.
    PNG files will be in use for other test cases.
    """
    def decode(self, file_name: str) -> Image:
        img: Image = open_image(samples_root_dir.joinpath(file_name))
        result = list(img.getdata())
        img.close()
        return result
    
    def decode_indexed(self, file_name: str, mode: str) -> Image:
        img: Image = open_image(samples_root_dir.joinpath(file_name))
        result = list(img.convert(mode).getdata())
        img.close()
        return result
    
    def test_rgb24(self):
        decoded_pixels = self.decode("rgb24.png")
        self.assertEqual(decoded_pixels, RGB24_TEST_DATA)
    
    def test_indexed_color(self):
        decoded_pixels = self.decode_indexed("indexed_color.png", "RGB")
        self.assertEqual(decoded_pixels, RGB24_TEST_DATA)
    
    def test_rgba32(self):
        decoded_pixels = self.decode("rgba32.png")
        self.assertEqual(decoded_pixels, RGBA32_TEST_DATA)

    def test_indexed_color_alpha(self):
        decoded_pixels = self.decode_indexed("indexed_color_alpha.png", "RGBA")
        self.assertEqual(decoded_pixels, RGBA32_TEST_DATA)
    
    def test_grayscale(self):
        decoded_pixels = self.decode("grayscale.png")
        self.assertEqual(decoded_pixels, GRAYSCALE_TEST_DATA)

    def test_grayscale_indexed(self):
        decoded_pixels = self.decode_indexed("indexed_grayscale.png", "L")
        self.assertEqual(decoded_pixels, GRAYSCALE_TEST_DATA)

    def test_grayscale_alpha(self):
        decoded_pixels = self.decode("grayscale_alpha.png")
        self.assertEqual(decoded_pixels, GRAYSCALE_ALPHA_TEST_DATA)

    def test_grayscale_indexed(self):
        decoded_pixels = self.decode_indexed("indexed_grayscale_alpha.png", "LA")
        self.assertEqual(decoded_pixels, GRAYSCALE_ALPHA_TEST_DATA)
