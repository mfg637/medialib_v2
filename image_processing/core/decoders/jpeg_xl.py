import subprocess
import pathlib
from image_processing.core.libvips.definitions import Image


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
        print("INFO: djxl stderr dump")
        print(stderr_text_data)
        raise RuntimeError("djxl failed")
