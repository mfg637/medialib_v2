import tempfile


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
