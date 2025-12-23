import PIL.Image
import PIL.ImageFile
import pathlib
import tempfile
import numpy
from . import (
    svg,
    jpeg_xl,
    video,
    YUV4MPEG2,
    frames_stream,
    ffmpeg_frames_stream,
)
from image_processing.libvips.definitions import Image
import pyvips


class DecodingError(Exception):
    pass


def open_image_vips(
    file_path: pathlib.Path,
    required_size: tuple[int, int] | None = None,
) -> Image:
    try:
        if required_size is not None:
            return Image.new_from_file(
                str(file_path),
                access="sequential",
                width=required_size[0],
                height=required_size[1],
            )
        else:
            return Image.new_from_file(
                str(file_path),
                access="sequential",
            )

    except pyvips.Error:
        # SVG fallback
        # if svg.is_svg(file_path):
        # return svg.decode(file_path, required_size)

        raise ValueError(f"Unsupported image format: {file_path}")


def open_image(
    file_path, required_size=None
) -> PIL.ImageFile.ImageFile | Image | ffmpeg_frames_stream.FFmpegFramesStream:
    if jpeg_xl.is_JPEG_XL(file_path):
        return jpeg_xl.decode(file_path)
    elif video.is_video(file_path):
        return video.open_video(file_path)
    else:
        return open_image_vips(file_path, required_size)


def get_image_format(file_path) -> str:
    if jpeg.is_JPEG(file_path):
        return "jpeg"
    elif avif.is_avif(file_path):
        return "avif"
    elif YUV4MPEG2.is_Y4M(file_path):
        return "y4m"
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
    if isinstance(img, frames_stream.FramesStream):
        first_frame = img.next_frame()
        img.close()
        return first_frame
    elif isinstance(img, Image):
        return PIL.Image.fromarray(img.numpy())
    else:
        return img


def open_image_as_vips_image(path: pathlib.Path) -> Image:
    img = open_image(path)

    if isinstance(img, frames_stream.FramesStream):
        first_frame = img.next_frame()
        img.close()

        if isinstance(first_frame, Image):
            return first_frame
        elif isinstance(first_frame, PIL.Image.Image):
            return Image.new_from_array(first_frame)
        else:
            raise TypeError(f"Unexpected frame type: {type(first_frame)}")

    if isinstance(img, PIL.Image.Image):
        return Image.new_from_array(img)

    if isinstance(img, Image):
        return img

    raise TypeError(f"Unexpected image type: {type(img)}")


def open_image_as_ndarray(path: pathlib.Path) -> numpy.ndarray:
    img = open_image_as_pil_image(path)
    return numpy.array(img)


def open_image_and_save_tmp_png(
    path: pathlib.Path,
) -> tempfile._TemporaryFileWrapper:
    img = open_image(path)
    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=True)
    if isinstance(img, frames_stream.FramesStream):
        first_frame = img.next_frame()
        first_frame.save(tmp_file, "PNG", compress_level=0)
        first_frame.close()
        img.close()
    elif isinstance(img, Image):
        img.pngsave(str(path))
    else:
        img.save(tmp_file, "PNG", compress_level=0)
        img.close()
    tmp_file.seek(0)
    return tmp_file
