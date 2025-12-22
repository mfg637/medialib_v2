from image_processing.libvips.definitions import (
    Image,
    Interpretation,
    BandFormat,
    BackgroundColor,
)
import pyvips
from typing import Callable
from PIL import ImageColor
import colorsys


def upcast_and_linearise(img: Image) -> Image:
    return img.cast(pyvips.enums.BandFormat.FLOAT).colourspace(
        pyvips.enums.Interpretation.SCRGB,
    )


VipsInterpretation = pyvips.enums.Interpretation
UCHAR_TYPE_SET = {pyvips.enums.BandFormat.UCHAR, "uchar"}
USHORT_TYPE_SET = {pyvips.enums.BandFormat.USHORT, "ushort"}


def get_sRGB_color(color: str, band_format: BandFormat) -> BackgroundColor:
    srgb_8bit_color: tuple[int, int, int] = ImageColor.getcolor(color, "RGB")
    if band_format in UCHAR_TYPE_SET:
        return srgb_8bit_color
    elif band_format in USHORT_TYPE_SET:
        return (
            srgb_8bit_color[0] << 8,
            srgb_8bit_color[1] << 8,
            srgb_8bit_color[2] << 8,
        )
    else:
        raise NotImplementedError(f"Unsupported band format: {band_format}")


def srgb8_to_linear(band_value: int) -> float:
    c = band_value / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def get_scRGB_color(
    color: str, band_format: BandFormat
) -> VipsBackgroundColor:
    srgb_8bit_color: tuple[int, int, int] = ImageColor.getcolor(color, "RGB")

    return tuple(srgb8_to_linear(c) for c in srgb_8bit_color)


def get_gray_color(color: str, band_format: BandFormat) -> BackgroundColor:
    gray_8bit_color: int = ImageColor.getcolor(color, "L")
    if band_format in UCHAR_TYPE_SET:
        return gray_8bit_color
    elif band_format in USHORT_TYPE_SET:
        return gray_8bit_color << 8
    elif band_format in {pyvips.enums.BandFormat.FLOAT, "float", "double"}:
        return srgb8_to_linear(gray_8bit_color)
    else:
        raise NotImplementedError(f"Unsupported band format: {band_format}")


def srgb8_to_cmyk(
    color_value: tuple[int, int, int],
) -> tuple[float, float, float, float]:
    r, g, b = [x / 255.0 for x in color_value]

    k = 1.0 - max(r, g, b)
    if k >= 1.0:
        return 0.0, 0.0, 0.0, 1.0

    c = (1.0 - r - k) / (1.0 - k)
    m = (1.0 - g - k) / (1.0 - k)
    y = (1.0 - b - k) / (1.0 - k)

    return c, m, y, k


def get_cmyk_color(color: str, band_format: BandFormat) -> BackgroundColor:
    srgb: tuple[int, int, int] = ImageColor.getcolor(color, "RGB")
    cmyk = srgb8_to_cmyk(srgb)

    if band_format is pyvips.enums.BandFormat.UCHAR:
        return tuple(int(round(x * 255)) for x in cmyk)
    elif band_format is pyvips.enums.BandFormat.USHORT:
        return tuple(int(round(x * 65535)) for x in cmyk)
    elif band_format in (
        pyvips.enums.BandFormat.FLOAT,
        pyvips.enums.BandFormat.DOUBLE,
    ):
        return cmyk
    else:
        raise NotImplementedError(f"Unsupported band format: {band_format}")


def srgb8_to_hsv(c: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = [x / 255.0 for x in c]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360.0, s, v


def get_hsv_color(color: str, band_format: BandFormat) -> BackgroundColor:
    srgb: tuple[int, int, int] = ImageColor.getcolor(color, "RGB")
    h, s, v = srgb8_to_hsv(srgb)

    if band_format in (
        pyvips.enums.BandFormat.FLOAT,
        pyvips.enums.BandFormat.DOUBLE,
    ):
        return h, s, v

    raise NotImplementedError("HSV should be represented as float in libvips")


def get_slab_color(color: str, band_format: BandFormat) -> BackgroundColor:
    if band_format is not pyvips.enums.BandFormat.SHORT:
        raise NotImplementedError("SLAB requires BandFormat.SHORT")

    # 1x1 sRGB image
    r, g, b = ImageColor.getcolor(color, "RGB")
    pixel = pyvips.Image.new_from_array(
        [[[r, g, b]]], interpretation=VipsInterpretation.SRGB
    )

    # Convert to LAB
    lab = pixel.colourspace(VipsInterpretation.LAB)

    # Cast to SLAB
    slab = lab.cast(pyvips.enums.BandFormat.SHORT)

    return tuple(int(slab(0, 0)[i]) for i in range(3))


def get_lab_color(color: str, band_format: BandFormat) -> BackgroundColor:
    lab_8bit_color: tuple[int, int, int] = ImageColor.getcolor(color, "LAB")
    if band_format is pyvips.enums.BandFormat.UCHAR:
        return lab_8bit_color
    elif band_format is pyvips.enums.BandFormat.USHORT:
        return (
            lab_8bit_color[0] << 8,
            lab_8bit_color[1] << 8,
            lab_8bit_color[2] << 8,
        )
    elif band_format is pyvips.enums.BandFormat.SHORT:
        return get_slab_color(color, band_format)
    else:
        raise NotImplementedError(f"Unsupported band format: {band_format}")


INTERPRETATION_TO_COLOR_VALUE: dict[
    Interpretation, Callable[[str, BandFormat], BackgroundColor]
] = {
    VipsInterpretation.SRGB: get_sRGB_color,
    VipsInterpretation.RGB: get_sRGB_color,
    VipsInterpretation.RGB16: get_sRGB_color,
    VipsInterpretation.SCRGB: get_scRGB_color,
    VipsInterpretation.B_W: get_gray_color,
    VipsInterpretation.GREY16: get_gray_color,
    VipsInterpretation.LAB: get_lab_color,
    VipsInterpretation.CMYK: get_cmyk_color,
    VipsInterpretation.HSV: get_hsv_color,
    VipsInterpretation.LABS: get_slab_color,
}
