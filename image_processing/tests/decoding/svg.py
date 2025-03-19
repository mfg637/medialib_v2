from django.test import SimpleTestCase
from image_processing import open_image
from image_processing.decoders import open_image_and_save_tmp_png as _open_image
from image_processing.config import samples_root_dir
from image_similarity_measures.evaluate import evaluation


class TestSVG(SimpleTestCase):
    def test_lossless_rgb(self):
        svg_file_path = samples_root_dir.joinpath("test.svg")
        img = open_image(svg_file_path)
        self.assertEqual(img.size, (32, 32))
        img.close()
        tmp_file = _open_image(svg_file_path)
        result = evaluation(
            str(samples_root_dir.joinpath("test.svg.png")),
            tmp_file.name,
            ["psnr",]
        )
        self.assertGreater(result["psnr"], 60.0)
        tmp_file.close()