from image_processing.libvips.definitions import Image
import pyvips

import subprocess
from . import frames_stream, ffmpeg

from .ffmpeg.parser import fps_calc


class FFmpegFramesStream(frames_stream.FramesStream):
    def __init__(self, file_name, original_filename=None):
        super().__init__(file_name)
        self._original_filename = original_filename
        data = ffmpeg.probe(file_name)

        video = ffmpeg.parser.find_video_stream(
            data, ffmpeg.parser.SPECIFY_VIDEO_STREAM.LAST
        )

        fps = ffmpeg.parser.get_fps(video)
        self._frame_time_ms = int(round(1 / fps * 1000))

        self._width = video["width"]
        self._height = video["height"]

        self._mode = "RGBA"

        self._duration = float(data["format"]["duration"])
        self._is_animated = self._duration > (1 / fps)

        commandline = [
            "ffmpeg",
            "-i",
            file_name,
            "-f",
            "image2pipe",
            "-map",
            "0:{}".format(video["index"]),
            "-pix_fmt",
            "rgba",
            "-an",
            "-r",
            str(fps),
            "-vcodec",
            "rawvideo",
            "-",
        ]
        self.process = subprocess.Popen(commandline, stdout=subprocess.PIPE)

    def next_frame(self) -> Image:
        if self._mode != "RGBA":
            raise NotImplementedError("mode is not supported", self._mode)

        frame_size = self._width * self._height * 4

        buffer = self.process.stdout.read(frame_size)
        if not buffer or len(buffer) < frame_size:
            raise EOFError()

        img = Image.new_from_buffer(
            buffer,
            "",
            width=self._width,
            height=self._height,
            bands=4,
            format="uchar",
        )

        img = img.copy(interpretation=pyvips.enums.Interpretation.SRGB)

        return img

    def close(self):
        self.process.stdout.close()
        self.process.terminate()

    @property
    def filename(self):
        if self._original_filename is not None:
            return self._original_filename
        return self._file_path
