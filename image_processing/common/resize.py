def bit_round(number, precision: int = 0):
    """
    Rounding numbers to a given precision, where presinion is a power of 2.
    If precision equals 0, then returns int(number);
    If presision great that 0, it rounds to a `precision` bits after point.
    If precision less than 0, then it rounds `precision` of less significant bits of integer.
    """
    scale = 1

    if precision > 0:
        scale = 2 ** precision
        number *= scale
    elif precision < 0:
        scale = 2 ** (precision * -1)
        number /= scale

    number = round(number)

    if precision > 0:
        number /= scale
    elif precision < 0:
        number *= scale

    if precision <= 0:
        return int(number)
    return number


def calc_fit_in_rect_downscale(
        original_size: tuple[int, int],
        fit_in_size: tuple[int, int],
        precision: int = 0
        ) -> tuple[float, int, int]:
    if original_size[0] > fit_in_size[0] or original_size[1] > fit_in_size[1]:
        aspect_ratio = original_size[0] / original_size[1]
        scale = 1
        new_size = original_size
        if aspect_ratio > 1:
            scale = original_size[0] / fit_in_size[0]
        else:
            scale = original_size[1] / fit_in_size[1]
        return (
            scale,
            bit_round(original_size[0] / scale, precision),
            bit_round(original_size[1] / scale, precision)
        )
    else:
        return (1.0, bit_round(original_size[0], precision), bit_round(original_size[1], precision))