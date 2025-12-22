import PIL.Image
import PIL.ImageColor
from image_processing.libvips.definitions import Image
from image_processing.transforms.color import INTERPRETATION_TO_COLOR_VALUE
import pyvips
from collections.abc import Sequence


def alpha_compose_pillow(
    image: PIL.Image.Image, background_color: str = "white"
) -> PIL.Image.Image:
    """
    Combines image with alpha-channel (RGBA) on background color.
    Returns PIL.Image.Image object with tree or one color channels.
    """
    if not image.has_transparency_data:
        return image

    new_mode = image.mode.replace("A", "")
    bg = PIL.Image.new(
        new_mode,
        image.size,
        PIL.ImageColor.getcolor(background_color, new_mode),
    )
    bg.paste(image, (0, 0), image)
    return bg


VipsInterpretation = pyvips.enums.Interpretation
VipsBlendMode = pyvips.enums.BlendMode


def alpha_compose_vips(image: Image, background_color: str = "white") -> Image:
    """
    Composite image with alpha channel over solid background color.
    Works for RGBA, YA, LABA, CMYKA, etc.
    """
    if not image.hasalpha():
        return image

    get_color = INTERPRETATION_TO_COLOR_VALUE.get(image.interpretation, None)
    if get_color is None:
        raise NotImplementedError(
            f"Not supported interpretation {image.interpretation}"
        )
    color = get_color(background_color, image.format)
    if isinstance(color, (int, float)):
        color = [float(color)]
    elif isinstance(color, Sequence):
        color = [float(value) for value in color]
    else:
        raise TypeError(f"Unexpected type {type(color)}")

    return image.flatten(background=color)


def alpha_compose(
    img: PIL.Image.Image | Image, background_color: str = "white"
) -> PIL.Image.Image | Image:
    """
    Composite image with alpha over background color.

    Supports:
    - PIL.Image.Image (Pillow)
    - pyvips.Image

    Background color is interpreted in sRGB space and converted
    to the image's color interpretation where applicable.
    """
    if isinstance(img, PIL.Image.Image):
        return alpha_compose_pillow(img, background_color)
    elif isinstance(img, Image):
        return alpha_compose_vips(img, background_color)
    else:
        raise TypeError(f"Unexpected image type: {type(img)}")
