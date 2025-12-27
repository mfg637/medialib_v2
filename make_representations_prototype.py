from image_processing.libvips.definitions import Image
from image_processing.transforms.color import upcast_and_linearise
from image_processing.transforms.resize import downscale
from image_processing.encoders import avif, webp

from typing import Callable
import pathlib
import argparse


def save_img_4096(csRGB_image: Image, source_file: pathlib.Path) -> None:
    output_file = source_file.with_stem(
        f"{source_file.stem} 4096"
    ).with_suffix(".avif")
    avif.encode(csRGB_image, output_file, quality=85)


def save_img_2048(csRGB_image: Image, source_file: pathlib.Path) -> None:
    output_file = source_file.with_stem(
        f"{source_file.stem} 2048"
    ).with_suffix(".avif")
    avif.encode(csRGB_image, output_file, quality=90, effort=3)


def save_img_1024(csRGB_image: Image, source_file: pathlib.Path) -> None:
    output_file = source_file.with_stem(
        f"{source_file.stem} 1024"
    ).with_suffix(".webp")
    webp.encode(
        csRGB_image,
        output_file,
        quality=95,
        smart_subsample=True,
        smart_deblock=True,
        effort=5,
    )


def save_img_512(csRGB_image: Image, source_file: pathlib.Path) -> None:
    output_file = source_file.with_stem(f"{source_file.stem} 512").with_suffix(
        ".webp"
    )
    webp.encode(csRGB_image, output_file, quality=90, smart_deblock=True)


def save_img_256(csRGB_image: Image, source_file: pathlib.Path) -> None:
    output_file = source_file.with_stem(f"{source_file.stem} 256").with_suffix(
        ".webp"
    )
    webp.encode(csRGB_image, output_file, quality=85, alpha_q=95)


def save_img_128(csRGB_image: Image, source_file: pathlib.Path) -> None:
    output_file = source_file.with_stem(f"{source_file.stem} 128").with_suffix(
        ".webp"
    )
    webp.encode(csRGB_image, output_file, quality=80, alpha_q=90)


# правильно ли называть его savers?
IMAGE_REPRESENTATION_SAVERS: dict[
    int, Callable[[Image, pathlib.Path], None]
] = {
    4096: save_img_4096,
    2048: save_img_2048,
    1024: save_img_1024,
    512: save_img_512,
    256: save_img_256,
    128: save_img_128,
}


def make_representations_from_source_file(source_file: pathlib.Path):
    PROCESSING_ORDER = [128, 256, 512, 1024, 2048, 4096]
    source_img: Image = Image.new_from_file(str(source_file))
    upcasted = upcast_and_linearise(source_img)

    for index, size in enumerate(PROCESSING_ORDER):
        print("processing representation", size)
        representation_upcasted = None
        if upcasted.width > size or upcasted.height > size:
            representation_upcasted = downscale(upcasted, (size, size))
        elif index > 0:
            prev_size = PROCESSING_ORDER[index - 1]
            if upcasted.width <= prev_size and upcasted.height <= prev_size:
                break
            else:
                representation_upcasted = upcasted
        else:
            representation_upcasted = upcasted
        save_representation: Callable[[Image, pathlib.Path], None] = (
            IMAGE_REPRESENTATION_SAVERS[size]
        )
        save_representation(representation_upcasted, source_file)


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("input_file", type=pathlib.Path)


if __name__ == "__main__":
    args = argument_parser.parse_args()
    input_file: pathlib.Path = args.input_file
    make_representations_from_source_file(input_file)
