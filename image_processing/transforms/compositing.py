import PIL.Image
import PIL.ImageColor
from image_processing.libvips.definitions import (
    Image,
    Interpretation,
    BandFormat,
)
from image_processing.transforms.color import INTERPRETATION_TO_COLOR_VALUE
import pyvips
from typing import Union, Sequence, Callable


def alpha_compose_pillow(
    image: PIL.Image.Image, background_color: str
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
VipsBackgroundColor = Union[float, Sequence[float]]


def alpha_compose_vips(
    image: Image, background_color: VipsBackgroundColor
) -> Image:
    """
    Composite image with alpha channel over solid background color.
    Works for RGBA, YA, LABA, CMYKA, etc.
    """

    if not image.hasalpha():
        return image

    alpha = image.extract_band(image.bands - 1)
    color = image.extract_band(0, n=image.bands - 1)

    background = color.new_from_image(background_color)

    composed = background.composite2(
        color.bandjoin(alpha),
        VipsBlendMode.OVER,
        x=0,
        y=0,
        compositing_space=color.interpretation,
        premultiplied=False,
    )

    return composed


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
        get_color = INTERPRETATION_TO_COLOR_VALUE.get(img.interpretation, None)
        if get_color is None:
            raise NotImplementedError(
                f"Not supported interpretation {img.interpretation}"
            )
        color = get_color(background_color, img.format)
        return alpha_compose_vips(img, color)
    else:
        raise TypeError(f"Unexpected image type: {type(img)}")
