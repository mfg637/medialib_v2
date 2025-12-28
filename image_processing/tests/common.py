from image_processing.common.utils import bit_round
from image_processing.transforms.calc_size import calc_fit_in_rect_downscale
from django.test import SimpleTestCase


class TestBitRound(SimpleTestCase):
    def test_int(self):
        self.assertEqual(bit_round(2.05), 2)
        self.assertEqual(bit_round(2.99), 3)

    def test_even_rounding(self):
        self.assertEqual(bit_round(0.5, precision=-1), 0)
        self.assertEqual(bit_round(1, precision=-1), 0)
        self.assertEqual(bit_round(1.5, precision=-1), 2)
        self.assertEqual(bit_round(2.5, precision=-1), 2)
        self.assertEqual(bit_round(3, precision=-1), 4)

    def test_quad_rounding(self):
        self.assertEqual(bit_round(7, precision=-2), 8)
        self.assertEqual(bit_round(5, precision=-2), 4)
        self.assertEqual(bit_round(1, precision=-2), 0)

    def test_float(self):
        self.assertEqual(bit_round(1.5, precision=1), 1.5)
        self.assertEqual(bit_round(1.25, precision=1), 1.0)
        self.assertEqual(bit_round(1.75, precision=1), 2.0)
        self.assertEqual(bit_round(2.1, precision=1), 2.0)


class TestFitDownscale(SimpleTestCase):
    def test_cl0_to_cl3(self):
        size = (15457, 44121)
        self.assertEqual(
            calc_fit_in_rect_downscale(size, (2048, 2048)),
            (21.54345703125, 717, 2048),
        )

    def test_cl0_to_cl3_even(self):
        size = (15457, 44121)
        self.assertEqual(
            calc_fit_in_rect_downscale(size, (2048, 2048), precision=-1),
            (21.54345703125, 718, 2048),
        )

    def test_cl4_to_cl3(self):
        size = (701, 555)
        self.assertEqual(
            calc_fit_in_rect_downscale(size, (2048, 2048)),
            (1.0, size[0], size[1]),
        )
