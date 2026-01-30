import numpy as np
import enum


class FirstStepDesizion(enum.IntEnum):
    RIGHT = 0
    DOWN = 1


def zigzag_scan(
    matrix: np.ndarray, first_step: FirstStepDesizion = FirstStepDesizion.RIGHT
) -> np.ndarray:
    """
    matrix: square array (nxn) (numpy.ndarray)
    first_step: RIGHT or DOWN
    """
    n = matrix.shape[0]
    index = 0
    result = np.zeros(n * n, matrix.dtype)

    for s in range(2 * n - 1):
        if s % 2 == first_step.value:
            i = min(s, n - 1)
            j = s - i
            while i >= 0 and j < n:
                result[index] = matrix[i, j]
                i -= 1
                j += 1
                index += 1
        else:
            j = min(s, n - 1)
            i = s - j
            while j >= 0 and i < n:
                result[index] = matrix[i, j]
                i += 1
                j -= 1
                index += 1
    return result
