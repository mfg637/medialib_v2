import PIL.Image
import pathlib
import tempfile
import numpy
import enum
from . import (
    jpeg,
    avif,
    svg,
    jpeg_xl,
    video,
)
from image_processing.libvips.definitions import Image
import pyvips


class DecodingError(Exception):
    pass


class AccessMode(enum.StrEnum):
    RANDOM = pyvips.enums.Access.RANDOM
    SEQUENTAL = pyvips.enums.Access.SEQUENTIAL


def open_image_vips(
    file_path: pathlib.Path | str,
    required_size: tuple[int, int] | None = None,
    access_mode: AccessMode = AccessMode.SEQUENTAL,
) -> Image:
    try:
        if required_size is not None:
            return Image.new_from_file(
                str(file_path),
                access=access_mode.value,
                width=required_size[0],
                height=required_size[1],
            )
        else:
            return Image.new_from_file(
                str(file_path),
                access=access_mode.value,
            )

    except pyvips.Error:
        raise ValueError(f"Unsupported image format: {file_path}")


def open_image(
    file_path: pathlib.Path | str,
    *,
    required_size: tuple[int, int] | None = None,
    access_mode: AccessMode = AccessMode.SEQUENTAL,
) -> Image:
    if jpeg_xl.is_JPEG_XL(file_path):
        return jpeg_xl.decode(file_path)
    elif video.is_video(file_path):
        return video.open_video(file_path)
    else:
        return open_image_vips(file_path, required_size, access_mode)


def get_image_format(file_path) -> str:
    if jpeg.is_JPEG(file_path):
        return "jpeg"
    elif avif.is_avif(file_path):
        return "avif"
    elif jpeg_xl.is_JPEG_XL(file_path):
        return "jpeg xl"
    elif video.is_video(file_path):
        return "video"
    else:
        pil_image_format = None
        try:
            pil_image_format = PIL.Image.open(file_path).format
            if pil_image_format is not None:
                return pil_image_format.lower()
            else:
                raise PIL.Image.UnidentifiedImageError(
                    "Unable to identify image format"
                )
        except PIL.Image.UnidentifiedImageError as e:
            if svg.is_svg(file_path):
                return "svg"
            else:
                raise e


def open_image_as_pil_image(path: pathlib.Path) -> PIL.Image.Image:
    img = open_image(path)
    if isinstance(img, Image):
        return PIL.Image.fromarray(img.numpy())
    else:
        return img


def open_image_as_vips_image(path: pathlib.Path) -> Image:
    img = open_image(path)

    if isinstance(img, PIL.Image.Image):
        return Image.new_from_array(img)

    if isinstance(img, Image):
        return img

    raise TypeError(f"Unexpected image type: {type(img)}")


def open_image_as_ndarray(path: pathlib.Path) -> numpy.ndarray:
    img = open_image_as_vips_image(path)
    return img.numpy()


def open_image_and_save_tmp_png(
    path: pathlib.Path,
) -> tempfile._TemporaryFileWrapper:
    img = open_image(path)
    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=True)
    if isinstance(img, Image):
        img.pngsave(str(path))
    else:
        img.save(tmp_file, "PNG", compress_level=0)
        img.close()
    tmp_file.seek(0)
    return tmp_file
