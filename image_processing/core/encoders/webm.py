from pathlib import Path
import tempfile
import subprocess
import logging

from image_processing.core.utils import run_subprocess, print_stderr
from image_processing.core.video.ffmpeg import probe, parser, transcoding

logger = logging.getLogger(__name__)


CONTAINER_OVERHEAD_KBPS = 150


def encode(
    source_file: Path | str,
    output_file: Path | str,
    min_size: int,
    max_size: int,
    fps_limit: int | float,
    quality: int | str = 32,
    copy_audio: bool = False,
    video_bitrate: int | str | None = None,
    max_video_bitrate: int | None = None,
    video_level: str | float | None = None,
    audio_bitrate: int = 96,
    rewrite: bool = True,
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
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_prefix = Path(tmp_dir).joinpath("pass_log")
        if data is None:
            data = probe(source_file)
        video_stream = parser.find_video_stream(data)
        width, height, src_min_size, src_max_size = parser.get_video_size(
            video_stream
        )
        tile_columns_log2 = transcoding.get_vp9_tile_columns(width)
        tile_rows_log2 = 0
        if height > width:
            tile_rows_log2, tile_columns_log2 = (
                tile_columns_log2,
                tile_rows_log2,
            )
        fps = parser.get_fps(video_stream)
        gop_size = round(fps * 10)
        vfilters = transcoding.build_vfilters(
            (width, height), (min_size, max_size), fps, fps_limit
        )
        if copy_audio:
            acodec = "copy"
        else:
            acodec = "libopus"
        pass_1_commandline = transcoding.build_vpx_vp9_commandline(
            source_file,
            output_file,
            quality,
            gop_size,
            tile_columns_log2,
            tile_rows_log2,
            log_prefix,
            vfilters,
            pass_index=1,
            audio_codec=None,
            video_bitrate=video_bitrate,
            audio_bitrate=audio_bitrate,
            max_video_bitrate=video_bitrate_limit,
            level=video_level,
        )
        try:
            proc_1 = run_subprocess(pass_1_commandline)
            proc_1.check_returncode()
        except subprocess.CalledProcessError as e:
            command_line_str = " ".join(
                [str(item) for item in pass_1_commandline]
            )
            logger.error(f"FFmpeg Pass 1 failed. Command: {command_line_str}")
            print_stderr(proc_1)
            raise e
        pass_2_commandline = transcoding.build_vpx_vp9_commandline(
            source_file,
            output_file,
            quality,
            gop_size,
            tile_columns_log2,
            tile_rows_log2,
            log_prefix,
            vfilters,
            pass_index=2,
            audio_codec=acodec,
            rewrite=rewrite,
            video_bitrate=video_bitrate,
            audio_bitrate=audio_bitrate,
            max_video_bitrate=video_bitrate_limit,
            level=video_level,
        )
        try:
            proc_2 = run_subprocess(pass_2_commandline)
            proc_2.check_returncode()
        except subprocess.CalledProcessError as e:
            if isinstance(output_file, Path):
                output_file.unlink(missing_ok=True)
            else:
                Path(output_file).unlink(missing_ok=True)
            command_line_str = " ".join(
                [str(item) for item in pass_2_commandline]
            )
            logger.error(f"FFmpeg Pass 2 failed. Command: {command_line_str}")
            print_stderr(proc_2)
            raise e
