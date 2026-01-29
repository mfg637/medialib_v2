from image_processing.core.video.ffmpeg import probe, parser, transcoding
from image_processing.core.transforms.calc_size import scale_down
from image_processing.core.utils import run_subprocess
from pathlib import Path


def encode(
    input_file: Path,
    output_file: Path,
    is_vfr: bool,
    *,
    quality: int = 24,
    rewrite: bool = False,
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
