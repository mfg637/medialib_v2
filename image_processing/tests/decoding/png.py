from django.test import SimpleTestCase
from image_processing import open_image
from PIL.Image import Image
from image_processing.config import samples_root_dir


class TestPNG(SimpleTestCase):
    def decode(self, file_name: str):
        img: Image = open_image(samples_root_dir.joinpath(file_name))
        result = list(img.getdata())
        img.close()
        return result
    
    def test_rgb24(self):
        decoded_pixels = self.decode("rgb24.png")
        expected_pixels = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
        self.assertEqual(decoded_pixels, expected_pixels)