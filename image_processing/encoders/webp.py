import enum
import pathlib
import pyvips
from image_processing.libvips.definitions import Image
from image_processing.transforms.color import has_embeded_icc


class WebPPreset(enum.StrEnum):
    DEFAULT = pyvips.enums.ForeignWebpPreset.DEFAULT
    PHOTO = pyvips.enums.ForeignWebpPreset.PHOTO
    PICTURE = pyvips.enums.ForeignWebpPreset.PICTURE
    DRAWING = pyvips.enums.ForeignWebpPreset.DRAWING
    ICON = pyvips.enums.ForeignWebpPreset.ICON
    TEXT = pyvips.enums.ForeignWebpPreset.TEXT


def encode(
    img: Image,
    saving_path: pathlib.Path | str,
    *,
    quality: int = 95,
    effort: int = 4,
    preset: WebPPreset = WebPPreset.DEFAULT,
    smart_subsample: bool = False,
    smart_deblock: bool = False,
    alpha_q: int = 100,
    lossless: bool = False,
) -> None:
    is_strip_safe = False
    if img.interpretation is pyvips.enums.Interpretation.SCRGB:
        saved_image = img.scRGB2sRGB(depth=8)
        is_strip_safe = True
    elif has_embeded_icc(img):
        if img.interpretation is pyvips.enums.Interpretation.SRGB:
            saved_image = img
        else:
            saved_image = img.icc_transform("srgb", embedded=True)
            is_strip_safe = True
    elif img.interpretation is pyvips.enums.Interpretation.SRGB:
        saved_image = img
        is_strip_safe = True
    else:
        saved_image = img.colourspace(pyvips.enums.Interpretation.SRGB)
        is_strip_safe = True

    if saved_image.format != pyvips.enums.BandFormat.UCHAR:
        saved_image = saved_image.cast(pyvips.enums.BandFormat.UCHAR)

    if lossless:
        saved_image.webpsave(
            str(saving_path),
            Q=100,
            effort=effort,
            alpha_q=100,
            strip=False,
            lossless=True,
        )
    else:
        saved_image.webpsave(
            str(saving_path),
            Q=quality,
            effort=effort,
            preset=preset.value,
            smart_subsample=smart_subsample,
            smart_deblock=smart_deblock,
            alpha_q=alpha_q,
            strip=is_strip_safe,
        )
