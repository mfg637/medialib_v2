from image_processing.libvips.definitions import Image


def debug_vips_image(**kwargs: Image) -> None:
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
    print(f"{name}: width: {value.width}, height: {value.height}")
    print(f"{name}: interpretation: {value.interpretation}")
    print(f"{name}: format: {value.format}")
    print(f"{name}: transparent: {has_alpha}")
