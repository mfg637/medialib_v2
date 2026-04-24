from image_processing.core.libvips.definitions import Image
from image_processing.core.transforms.color import upcast_and_linearise
from image_processing.core.transforms.resize import downscale

from typing import Optional
import pyvips
import pathlib
import argparse
import enum


class PNG_SavingBitDepth(enum.IntEnum):
    STANDARD = 8
    HIGH_PRECISION = 16


def save_as_png(
    img: Image, saving_path: pathlib.Path, bit_depth: PNG_SavingBitDepth
) -> None:
    saved_image = img.scRGB2sRGB(depth=bit_depth.value)
    saved_image.pngsave(str(saving_path), bitdepth=bit_depth.value)


def save_as_avif(
    img: Image, saving_path: pathlib.Path, quality: int = 90
) -> None:
    saved_image = img.scRGB2sRGB(depth=16)
    saved_image.heifsave(
        str(saving_path),
        compression=pyvips.enums.ForeignHeifCompression.AV1,
        Q=quality,
        bitdepth=10,
        effort=2,
    )


def save_as_webp(
    img: Image, saving_path: pathlib.Path, quality: int = 95
) -> None:
    saved_image = img.scRGB2sRGB(depth=8)
    saved_image.webpsave(str(saving_path), Q=quality)


def save_image(
    img: Image, output_file: pathlib.Path, quality: Optional[int] = None
) -> None:
    ext = output_file.suffix.lower()

    if ext == ".png":
        save_as_png(img, output_file, PNG_SavingBitDepth.HIGH_PRECISION)
    elif ext == ".avif":
        if quality is not None:
            save_as_avif(img, output_file, quality)
        else:
            save_as_avif(img, output_file)
    elif ext == ".webp":
        if quality is not None:
            save_as_webp(img, output_file, quality)
        else:
            save_as_webp(img, output_file)


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("input_file", type=pathlib.Path)
argument_parser.add_argument("output_file", type=pathlib.Path)
argument_parser.add_argument("width", type=int)
argument_parser.add_argument("height", type=int)


if __name__ == "__main__":
    args = argument_parser.parse_args()
    input_file: pathlib.Path = args.input_file
    output_file: pathlib.Path = args.output_file
    target_width: int = args.width
    target_height: int = args.height

    source_img: Image = Image.new_from_file(str(input_file))
    img = upcast_and_linearise(source_img)
    downscaled_image = downscale(img, (target_width, target_height))
    save_image(downscaled_image, output_file)
