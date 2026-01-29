from image_processing.core.utils import bit_round
from image_processing.core.transforms.calc_size import (
    calc_fit_in_rect_downscale,
    scale_down,
)
from image_processing.core.video.ffmpeg.transcoding import get_vp9_tile_columns
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


class ScaleDownTest(SimpleTestCase):
    def test_scale_down_no_changes(self):
        source = (720, 480)
        limits = (480, 1080)
        result = scale_down(source, limits, size_precision=-1)
        self.assertEqual(result, (720, 480))

    def test_scale_down_too_small(self):
        source = (320, 240)
        limits = (480, 1280)
        result = scale_down(source, limits, size_precision=-1)
        self.assertEqual(result, source)

    def test_scale_down_too_large(self):
        source = (3840, 2160)
        limits = (1080, 1920)
        result = scale_down(source, limits, size_precision=-1)
        self.assertEqual(result, (1920, 1080))

    def test_scale_down_portrait(self):
        source = (1080, 1920)
        limits = (720, 1280)
        result = scale_down(source, limits, size_precision=-1)
        self.assertEqual(result, (720, 1280))

    def test_scale_down_precision_rounding(self):
        source = (1001, 501)
        limits = (480, 1080)
        result = scale_down(source, limits, size_precision=-1)
        self.assertEqual(result[0] % 2, 0)
        self.assertEqual(result[1] % 2, 0)
        self.assertEqual(result, (960, 480))


class TestTranscodingPureFunctions(SimpleTestCase):
    def test_tile_columns_logic(self):
        self.assertEqual(get_vp9_tile_columns(640), 1)
        self.assertEqual(get_vp9_tile_columns(1280), 2)
        self.assertEqual(get_vp9_tile_columns(1920), 2)
        self.assertEqual(get_vp9_tile_columns(3840), 3)
