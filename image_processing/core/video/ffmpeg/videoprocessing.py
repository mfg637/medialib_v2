import tempfile
from image_processing.core.compatibility_level import (
    cl3_video_width,
    cl3_video_height,
)


def ffmpeg_set_fps_commandline(fps):
    return ["-r", str(fps)]


def limit_fps(fps, limit_value=30):
    src_fps_valid = True
    if fps > limit_value:
        src_fps_valid = False
        while fps > limit_value:
            fps /= 2
    return fps, src_fps_valid


def ffmpeg_get_passfile_prefix():
    passfilename = ""
    with tempfile.NamedTemporaryFile() as f:
        passfilename = f.name
    return passfilename


CL3_FFMPEG_SCALE_COMMANDLINE = [
    "-vf",
    "scale='min({},iw)':'min({},ih)':force_original_aspect_ratio=decrease".format(
        cl3_video_width, cl3_video_height
    ),
]
