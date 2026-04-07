import numpy
import logging
import subprocess
import pathlib
import tempfile
import numbers
import typing
from collections.abc import Sequence
from fractions import Fraction

logger = logging.getLogger(__name__)


def debug_ndarray(use_print=False, **kwargs: numpy.ndarray) -> None:
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
    if use_print:
        print(f"{name}: dtype: {value.dtype}, shape: {value.shape}")
        print(f"{name}: min: {value.min()}, max: {value.max()}")
        print(
            f"{name}: average: {numpy.average(value)}, deviation: {value.std()}"
        )
    elif logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "%s: dtype: %s, shape: %s", name, value.dtype, value.shape
        )
        logger.debug("%s: min: %d, max: %d", name, value.min(), value.max())
        logger.debug(
            "%s: average: %d, deviation: %d",
            name,
            numpy.average(value),
            value.std(),
        )


def run_subprocess(
    commandline: list[str], log_stdout=False, capture_out=True
) -> subprocess.CompletedProcess:
    logger.debug("starting process")
    result = subprocess.run(commandline, capture_output=capture_out)
    logger.debug("process executed and done")
    if capture_out:
        stderr_message = result.stderr.decode("utf-8").splitlines()
        for line in stderr_message:
            logger.debug("stderr: {}".format(line))
        if log_stdout:
            stdout_message = result.stdout.decode("utf-8").splitlines()
            for line in stdout_message:
                logger.debug("stdout: {}".format(line))
    logger.debug("all logging is done")
    return result


def print_stderr(proc: subprocess.CompletedProcess) -> None:
    stderr_message = proc.stderr.decode("utf-8").splitlines()
    for line in stderr_message:
        logger.debug("stderr: {}".format(line))


def bit_round(number: int | float, precision: int = 0) -> int | float:
    scale = 1

    if precision > 0:
        scale = 2**precision
        number *= scale
    elif precision < 0:
        scale = 2 ** (precision * -1)
        number /= scale

    number = round(number)

    if precision > 0:
        number /= scale
    elif precision < 0:
        number *= scale

    return number


SourceType = typing.Union[str, pathlib.Path, bytes, bytearray]


class InputSourceFacade:
    def __init__(self, source: SourceType, suffix=None, writer=None):
        self._source = source
        self._tmpfile = None
        self.suffix = suffix
        self.writer = writer

    def get_file_path(self) -> pathlib.Path:
        file_path = pathlib.Path()
        if isinstance(self._source, str):
            file_path = pathlib.Path(self._source)
        elif isinstance(self._source, pathlib.Path):
            file_path = self._source
        else:
            self._tmpfile = tempfile.NamedTemporaryFile(
                delete=True, suffix=self.suffix
            )
            file_path = pathlib.Path(self._tmpfile.name)
            if self.writer is None:
                self._tmpfile.write(self._source)
            else:
                self.writer(self._tmpfile)
        return file_path

    def get_file_str(self) -> str:
        file_path = ""
        if isinstance(self._source, str):
            file_path = self._source
        elif isinstance(self._source, pathlib.Path):
            file_path = str(self._source)
        else:
            self._tmpfile = tempfile.NamedTemporaryFile(
                delete=True, suffix=self.suffix
            )
            file_path = self._tmpfile.name
            if self.writer is None:
                self._tmpfile.write(self._source)
            else:
                self.writer(self._tmpfile)
        return file_path

    def get_bytes(self) -> bytes | bytearray:
        if isinstance(self._source, (bytes, bytearray)):
            return self._source
        else:
            if type(self._source) is str:
                file_path = pathlib.Path(self._source)
            elif isinstance(self._source, pathlib.Path):
                file_path = self._source
            else:
                raise TypeError(f"Unexpected type: {type(self._source)}")
            binary_data = file_path.read_bytes()
            return binary_data

    def close(self):
        if self._tmpfile is not None:
            self._tmpfile.close()
            self._tmpfile = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        self.close()
        return True


def check_is_fractions(value):
    return isinstance(value, Fraction) or (
        isinstance(value, Sequence)
        and len(value) == 2
        and isinstance(value[0], numbers.Rational)
        and isinstance(value[1], numbers.Rational)
        and value[1] != 0
    )


def fractions_to_float(
    fraction: Fraction | tuple[int, int] | typing.Any,
) -> float:
    if isinstance(fraction, Fraction):
        return fraction.numerator / fraction.denominator
    elif isinstance(fraction, Sequence):
        return fraction[0] / fraction[1]
    else:
        return float(fraction)


def to_fractions_or_float(value):
    if check_is_fractions(value):
        if isinstance(value, Fraction):
            return value
        return Fraction(*value)
    elif isinstance(value, (int, float)):
        return value
    else:
        return float(value)


def to_float(value):
    if check_is_fractions(value):
        return fractions_to_float(value)
    elif isinstance(value, (int, float)):
        return value
    else:
        return float(value)


def format_number(value):
    value = to_fractions_or_float(value)
    if isinstance(value, Fraction):
        return str(value)
    else:
        return f"{value:.3f}"
