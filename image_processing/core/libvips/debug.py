import logging
from .definitions import Image

logger = logging.getLogger(__name__)


def debug_vips_image(use_print=False, **kwargs: Image) -> None:
    if len(kwargs) != 1:
        raise ValueError(
            "Function vips_image_debug expects exactly one named argument"
        )

    name, value = next(iter(kwargs.items()))

    if not isinstance(value, Image):
        raise TypeError(
            (
                f"Argument {name} expected to be "
                f"image_processing.libvips.definitions.Image, "
                f"not {type(value)}"
            )
        )

    has_alpha: bool = value.hasalpha()
    if use_print:
        print(f"{name}: width: {value.width}, height: {value.height}")
        print(f"{name}: interpretation: {value.interpretation}")
        print(f"{name}: format: {value.format}")
        print(f"{name}: transparent: {has_alpha}")
        print(f"{name}: min: {value.min()}, max: {value.max()}")
        print(f"{name}: average: {value.avg()}")
    else:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "%s: width: %d, height: %d", name, value.width, value.height
            )
            logger.debug("%s: interpretation: %s", name, value.interpretation)
            logger.debug("%s: format: %s", name, value.format)
            logger.debug("%s: transparent: %s", name, has_alpha)
            logger.debug(
                "%s: min: %s, max: %s", name, value.min(), value.max()
            )
            logger.debug("%s: average: %s", name, value.avg())
