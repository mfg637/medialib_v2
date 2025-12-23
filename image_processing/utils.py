import numpy


def debug_ndarray(**kwargs: numpy.ndarray) -> None:
    if len(kwargs) != 1:
        raise ValueError(
            "Function vips_image_debug expects exactly one named argument"
        )

    name, value = next(iter(kwargs.items()))

    if not isinstance(value, numpy.ndarray):
        raise TypeError(
            (
                f"Argument {name} expected to be "
                f"numpy.ndarray, "
                f"not {type(value)}"
            )
        )

    print(f"{name}: dtype: {value.dtype}, shape: {value.shape}")
    print(f"{name}: min: {value.min()}, max: {value.max()}")
    print(f"{name}: average: {numpy.average(value)}, deviation: {value.std()}")
