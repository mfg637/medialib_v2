import subprocess
import pathlib
import logging
from image_processing.core.libvips.definitions import Image

logger = logging.getLogger(__name__)


def is_JPEG_XL(file_path: pathlib.Path | str):
    with open(file_path, "rb") as f:
        header = f.read(7)
    return header == b"\x00\x00\x00\x0cJXL" or header[:2] == b"\xff\x0a"


def decode(file: pathlib.Path | str) -> Image:
    proc = subprocess.Popen(
        ["djxl", file, "-", "--output_format", "pam"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = proc.communicate()

    if proc.returncode == 0:
        return Image.new_from_buffer(stdout, "")
    else:
        stderr_text_data = stderr.decode(errors="replace")
        logger.error("INFO: djxl stderr dump")
        logger.error(stderr_text_data)
        raise RuntimeError("djxl failed")
