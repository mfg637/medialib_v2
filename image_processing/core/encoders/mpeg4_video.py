import subprocess
import logging
from image_processing.core.video.ffmpeg import probe, parser, transcoding
from image_processing.core.transforms.calc_size import scale_down
from image_processing.core.utils import run_subprocess, print_stderr
from pathlib import Path

logger = logging.getLogger(__name__)
CONTAINER_OVERHEAD_KBPS = 200


def encode(
    input_file: Path,
    output_file: Path,
    is_vfr: bool,
    *,
    quality: int = 24,
    rewrite: bool = True,
    min_size=1080,
    max_size=1920,
    data: dict | None = None,
) -> None:
    if data is None:
        data = probe(input_file)
    video_stream = parser.find_video_stream(data)
    original_width, original_height, src_min_size, src_max_size = (
        parser.get_video_size(video_stream)
    )
    downscale = scale_down(
        (original_width, original_height), (min_size, max_size)
    )
    vfilters = transcoding.build_x264_video_filters(
        original_width, original_height, downscale, is_vfr
    )

    if is_vfr:
        gop_size = 120  # 60 frames per seconds * 2 seconds
    else:
        gop_size = int(round(parser.get_fps(video_stream))) * 2

    commandline = transcoding.build_x264_commandline(
        input_file, output_file, quality, gop_size, vfilters, rewrite
    )

    proc = run_subprocess(commandline)
    proc.check_returncode()


def encode_av1(
    source_file: Path | str,
    output_file: Path | str,
    min_size: int,
    max_size: int,
    fps_limit: int | float,
    quality: int | str = 24,
    copy_audio: bool = False,
    video_bitrate: int | str | None = None,
    max_video_bitrate: int | None = None,
    audio_bitrate: int = 128,
    rewrite: bool = True,
    preset: int = 4,
    data: dict | None = None,
):
    video_bitrate_limit = None
    if max_video_bitrate is not None:
        audio_reserve = int(audio_bitrate * 1.4)
        video_bitrate_limit = max(
            int(max_video_bitrate - audio_reserve - CONTAINER_OVERHEAD_KBPS),
            1000,
        )
        if isinstance(video_bitrate, int):
            video_bitrate_limit = min(video_bitrate * 2, video_bitrate_limit)

    if data is None:
        data = probe(source_file)
    video_stream = parser.find_video_stream(data)
    width, height, _, _ = parser.get_video_size(video_stream)

    cols = transcoding.get_vp9_tile_columns(width)
    rows = 0
    if height > width:
        cols, rows = rows, cols

    fps = parser.get_fps(video_stream)
    gop_size = round(fps * 10)
    vfilters = transcoding.build_vfilters(
        (width, height), (min_size, max_size), fps, fps_limit
    )

    acodec = "copy" if copy_audio else "libopus"

    commandline = transcoding.build_svt_av1_commandline(
        source_file,
        output_file,
        quality,
        gop_size,
        vfilters,
        tile_columns=cols,
        tile_rows=rows,
        audio_codec=acodec,
        audio_bitrate=audio_bitrate,
        rewrite=rewrite,
    )

    try:
        proc = run_subprocess(commandline)
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        Path(output_file).unlink(missing_ok=True)
        command_line_str = " ".join([str(item) for item in commandline])
        logger.error(
            f"FFmpeg AV1 encoding failed. Command: {command_line_str}"
        )
        print_stderr(proc)
        raise e
