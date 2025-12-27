import enum
import pathlib
import pyvips
from image_processing.libvips.definitions import Image, Interpretation


class SubsamplingMode(enum.StrEnum):
    ENABLED = "on"
    DISABLED = "off"
    AUTO = "auto"
    YUV444 = DISABLED
    YUV420 = ENABLED


class Encoder(enum.StrEnum):
    AUTO = pyvips.enums.ForeignHeifEncoder.AUTO
    AOM = pyvips.enums.ForeignHeifEncoder.AOM
    SVT = pyvips.enums.ForeignHeifEncoder.SVT
    RAV1E = pyvips.enums.ForeignHeifEncoder.RAV1E


def encode(
    img: Image,
    saving_path: pathlib.Path | str,
    *,
    quality: int = 90,
    effort: int = 4,
    subsample_mode: SubsamplingMode = SubsamplingMode.AUTO,
    encoder: Encoder = Encoder.AOM,
) -> None:
    INTERPRETATIONS_ENUM = pyvips.enums.Interpretation
    AVIF_COMPATIBLE_MODES: set[Interpretation] = {
        INTERPRETATIONS_ENUM.SRGB,
        INTERPRETATIONS_ENUM.RGB,
        INTERPRETATIONS_ENUM.RGB16,
        INTERPRETATIONS_ENUM.B_W,
        INTERPRETATIONS_ENUM.GREY16,
    }
    if img.interpretation is pyvips.enums.Interpretation.SCRGB:
        saved_image = img.scRGB2sRGB(depth=16)
    elif img.interpretation in AVIF_COMPATIBLE_MODES:
        saved_image = img
    else:
        saved_image = img.colourspace(INTERPRETATIONS_ENUM.SRGB)

    saved_image.heifsave(
        str(saving_path),
        compression="av1",
        Q=quality,
        bitdepth=10,
        effort=effort,
        subsample_mode=subsample_mode.value,
        encoder=encoder.value,
    )
