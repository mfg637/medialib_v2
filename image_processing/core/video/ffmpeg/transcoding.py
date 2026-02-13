from fractions import Fraction
from pathlib import Path
from image_processing.core.transforms.calc_size import scale_down
from image_processing.core.utils import (
    format_number,
    run_subprocess,
    bit_round,
)
from typing import Optional
from image_processing.config import encoding_threads
import math
import os


def mp4_copy_commandline(
    source_file: Path | str, output_file: Path | str
) -> list[str]:
    return [
        "ffmpeg",
        "-i",
        str(source_file),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(output_file),
    ]


def mp4_copy_video(source_file: Path | str, output_file: Path | str):
    commandline = mp4_copy_commandline(source_file, output_file)
    proc = run_subprocess(commandline)
    proc.check_returncode()


def make_size_even(size: int | float) -> int:
    return int(bit_round(size, -1))


def build_x264_video_filters(
    width: int,
    height: int,
    downscale: Optional[tuple[int, int]] = None,
    is_vfr: bool = False,
) -> str:
    """
    Builds specific filter graph intended for using with x264 encoder
    keeps sides even and transparancy aware.
    """
    target_w: int
    target_h: int
    target_w, target_h = downscale if downscale else (width, height)

    target_w = make_size_even(target_w)
    target_h = make_size_even(target_h)

    v_stream = "[0:v:0]"
    v_filters = f"scale={target_w}:{target_h}"

    if is_vfr:
        v_filters += ",fps=60"

    filter_complex = (
        f"{v_stream}{v_filters}[v];"
        f"color=c=white:s={target_w}x{target_h}[bg];"
        f"[bg][v]overlay=shortest=1:format=yuv420"
    )

    return filter_complex


def build_x264_commandline(
    input_file: Path | str,
    output_file: Path | str,
    quality: str | int,
    gop_size: int | str,
    vfilters: str,
    rewrite: bool = False,
) -> list[str]:
    commandline = [
        "ffmpeg",
        "-y" if rewrite else None,
        "-i",
        str(input_file),
        "-movflags",
        "+faststart",
        "-filter_complex",
        vfilters,
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        "-crf",
        str(quality),
        "-preset",
        "slow",
        "-g",
        str(gop_size),
        str(output_file),
    ]
    if commandline[1] is None:
        commandline.pop(1)
    return commandline


def get_vp9_tile_columns(width: int) -> int:
    """
    Calculates -tile-columns value for VPX-VP9 encoder.
    Minimum tile width: 256px.
    Tile count must be power of two.
    """
    max_tiles = width // 256

    if max_tiles <= 1:
        return 0

    exponent = int(math.log2(max_tiles))

    return min(exponent, 6)


def build_vfilters(
    source_size: tuple[int, int],
    size_limit: Optional[tuple[int, int]],
    source_fps: int | float | Fraction,
    fps_limit: int | float,
) -> Optional[str]:
    target_w: int
    target_h: int
    target_w, target_h = (
        scale_down(source_size, size_limit) if size_limit else source_size
    )

    target_w = make_size_even(target_w)
    target_h = make_size_even(target_h)
    limit_with_threshold = fps_limit * 1.05

    video_filters = []
    if target_w != source_size[0] or target_h != source_size[1]:
        video_filters.append(f"scale={target_w}:{target_h}:flags=lanczos")
    if source_fps > limit_with_threshold:
        target_fps = source_fps
        while target_fps > limit_with_threshold:
            target_fps /= 2
        video_filters.append(f"fps={format_number(target_fps)}")
    if video_filters:
        return ",".join(video_filters)
    else:
        return None


def build_vpx_vp9_commandline(
    input_file: Path | str,
    output_file: Path | str,
    quality: str | int,
    gop_size: int | str,
    tile_columns: int | str,
    pass_log_prefix: Path | str,
    vfilters: Optional[str],
    *,
    pass_index: int,
    pixel_format: str = "yuv420p",
    audio_codec: str | None = "libopus",
    audio_bitrate: int | str = 96,
    video_bitrate: int | str | None = None,
    max_video_bitrate: int | str | None = None,
    cpu_used: int | str = 4,
    level: str | float | None = None,
    rewrite: bool = False,
) -> list[str]:
    commandline = ["ffmpeg"]
    if rewrite or pass_index == 1:
        commandline += ["-y"]
    commandline += [
        "-loglevel",
        "warning",
        "-i",
        input_file,
        "-pass",
        str(pass_index),
    ]
    if vfilters is not None:
        commandline += [
            "-vf",
            vfilters,
        ]
    if level is not None:
        commandline += ["-level", str(level)]
    if isinstance(video_bitrate, int):
        video_bitrate_str: str = f"{video_bitrate}k"
    elif video_bitrate is None:
        video_bitrate_str = "0"
    elif isinstance(video_bitrate, str):
        video_bitrate_str = video_bitrate
    commandline += [
        "-pix_fmt",
        pixel_format,
        "-c:v",
        "libvpx-vp9",
        "-crf",
        str(quality),
        "-b:v",
        video_bitrate_str,
        "-profile:v",
        "0",
        "-cpu-used",
        str(cpu_used),
        "-row-mt",
        "1",
        "-threads",
        str(encoding_threads),
        "-tile-columns",
        str(tile_columns),
        "-g",
        str(gop_size),
        "-passlogfile",
        str(pass_log_prefix),
    ]
    if isinstance(max_video_bitrate, int):
        max_video_bitrate_str: str = f"{max_video_bitrate}k"
        buff_size_str: str = f"{max_video_bitrate * 2}k"
    elif isinstance(max_video_bitrate, str):
        max_video_bitrate_str = max_video_bitrate
        buff_size_str = max_video_bitrate_str
    if max_video_bitrate is not None:
        commandline += [
            "-maxrate",
            max_video_bitrate_str,
            "-bufsize",
            buff_size_str,
        ]
    if audio_codec is None or pass_index == 1:
        commandline += ["-an"]
    elif audio_codec == "copy":
        commandline += ["-c:a", "copy"]
    else:
        commandline += ["-c:a", audio_codec, "-b:a", f"{audio_bitrate}k"]
    if pass_index == 1:
        commandline += [
            "-f",
            "null",
            "NUL" if os.name == "nt" else "/dev/null",
        ]
    else:
        commandline += [
            "-f",
            "webm",
            str(output_file),
        ]
    return commandline
