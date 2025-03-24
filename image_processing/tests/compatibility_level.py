from image_processing.common import compatibility_level as cl
from image_processing.common import file_format as ff
from django.test import SimpleTestCase


class CompatiblityLevelTest(SimpleTestCase):
    def test_cl4(self):
        width = 894
        height = 458
        self.assertEqual(cl.get_compatibility_level_by_size(width, height), 4)
        size = (width, height)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.JPEG), 4)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.PNG), 4)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.WEBP), 3)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.AVIF), 2)

    def test_cl3(self):
        width = 742
        height = 1685
        self.assertEqual(cl.get_compatibility_level_by_size(width, height), 3)
        size = (width, height)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.JPEG), 3)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.WEBP), 3)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.AVIF), 2)
    
    def test_cl2(self):
        width = 3275
        height = 2087
        self.assertEqual(cl.get_compatibility_level_by_size(width, height), 2)
        size = (width, height)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.JPEG), 2)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.WEBP), 2)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.AVIF), 2)

    def test_cl1(self):
        width = 7593
        height = 1246
        self.assertEqual(cl.get_compatibility_level_by_size(width, height), 1)
        size = (width, height)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.JPEG), 1)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.WEBP), 1)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.AVIF), 1)

    def test_cl0(self):
        width = 19321
        height = 29301
        self.assertEqual(cl.get_compatibility_level_by_size(width, height), 0)
        size = (width, height)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.JPEG), 0)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.WEBP), 0)
        self.assertEqual(cl.get_image_compatibility_level(size, ff.FormatEnum.AVIF), 0)

    def test_respesentations_from_cl0_png(self):
        width = 29301
        height = 19321
        size = (width, height)
        representations = cl.calc_representations_format(size, ff.FormatEnum.PNG)
        self.assertEqual(
            representations[0],
            (ff.FormatEnum.AVIF, width, height)
        )
        self.assertEqual(
            representations[1],
            (ff.FormatEnum.AVIF, 7325, 4830)
        )
        self.assertEqual(
            representations[2],
            (ff.FormatEnum.AVIF, 3663, 2415)
        )
        self.assertEqual(
            representations[3],
            (ff.FormatEnum.WEBP, 1831, 1208)
        )
        self.assertEqual(
            representations[4],
            (ff.FormatEnum.JPEG, 916, 604)
        )
    
    def test_respesentations_from_cl0_jpeg(self):
        width = 29301
        height = 19321
        size = (width, height)
        representations = cl.calc_representations_format(size, ff.FormatEnum.JPEG)
        self.assertEqual(
            representations[0],
            (ff.FormatEnum.JPEG, width, height)
        )
        self.assertEqual(
            representations[1],
            (ff.FormatEnum.AVIF, 7325, 4830)
        )
        self.assertEqual(
            representations[2],
            (ff.FormatEnum.AVIF, 3663, 2415)
        )
        self.assertEqual(
            representations[3],
            (ff.FormatEnum.WEBP, 1831, 1208)
        )
        self.assertEqual(
            representations[4],
            (ff.FormatEnum.JPEG, 916, 604)
        )
    
    def test_representatons_from_svg(self):
        width = 7593
        height = 1246
        size = (width, height)
        representations = cl.calc_representations_format(size, ff.FormatEnum.SVG)
        self.assertEqual(
            representations[0],
            (ff.FormatEnum.SVG, width, height)
        )
        self.assertEqual(
            representations[1],
            (ff.FormatEnum.AVIF, width, height)
        )
        self.assertEqual(
            representations[2],
            (ff.FormatEnum.AVIF, 3796, 623)
        )
        self.assertEqual(
            representations[3],
            (ff.FormatEnum.WEBP, 1898, 312)
        )
        self.assertEqual(
            representations[4],
            (ff.FormatEnum.JPEG, 949, 156)
        )
