from image_processing.core.libvips.definitions import Image
from image_processing.core.video import ffmpeg
from image_processing.core.utils import run_subprocess
import pathlib
import random
import pyvips
from typing import Optional


front_cover_filenames = {"cover.jpg", "front.jpg"}


def find_video_stream(data) -> tuple[dict, bool]:
    first_video = None
    last_attached_picture = None
    attached_front_cover = None
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            if first_video is None:
                first_video = stream
            elif stream["disposition"]["attached_pic"] == 1:
                last_attached_picture = stream
                if stream["tags"]["filename"] in front_cover_filenames:
                    attached_front_cover = stream
    if attached_front_cover is not None:
        return attached_front_cover, True
    elif last_attached_picture is not None:
        return last_attached_picture, True
    elif first_video is not None:
        return first_video, False
    else:
        raise ValueError("No video streams found")


def decode(
    filepath: pathlib.Path | str, parsed_data: Optional[dict] = None
) -> Image:
    """
    Extract a representative static preview frame from a video file.

    Priority:
    1. Attached cover art (front.jpg / cover.jpg)
    2. Any attached picture
    3. Random thumbnail frame from the main video stream

    Returns:
        pyvips.Image in sRGB interpretation
    """
    data = parsed_data
    if data is None:
        data = ffmpeg.probe(filepath)

    video_stream, is_attached_picture = find_video_stream(data)
    stream_index = video_stream["index"]
    width = video_stream["width"]
    height = video_stream["height"]
    proc_data = None
    channel_count = 3
    pix_fmt = "rgb24"
    if is_attached_picture:
        commandline = [
            "ffmpeg",
            "-i",
            str(filepath),
            "-map",
            f"0:{stream_index}",
            "-frames:v",
            "1",
            "-pix_fmt",
            pix_fmt,
            "-f",
            "rawvideo",
            "-",
        ]
        proc_data = run_subprocess(commandline)
    else:
        duration = float(data["format"]["duration"])
        start_duration = duration * 0.1
        duration_range = duration * 0.8
        seek_timestamp = duration_range * random.random() + start_duration
        if "yuva" in video_stream["pix_fmt"]:
            channel_count = 4
            pix_fmt = "rgba"
        commandline = [
            "ffmpeg",
            "-ss",
            str(seek_timestamp),
            "-i",
            str(filepath),
            "-map",
            f"0:{stream_index}",
            "-vf",
            f"thumbnail,scale={width}:{height}",
            "-frames:v",
            "1",
            "-pix_fmt",
            pix_fmt,
            "-f",
            "rawvideo",
            "-",
        ]
        proc_data = run_subprocess(commandline)

    expected_size = width * height * channel_count
    if proc_data.returncode != 0:
        raise RuntimeError("Error executing ffmpeg command")
    if len(proc_data.stdout) != expected_size:
        raise ValueError("Unexpected raw frame size")

    img = Image.new_from_memory(
        proc_data.stdout,
        width=width,
        height=height,
        bands=channel_count,
        _format=pyvips.enums.BandFormat.UCHAR,
    )

    img = img.copy(interpretation=pyvips.enums.Interpretation.SRGB)

    return img
