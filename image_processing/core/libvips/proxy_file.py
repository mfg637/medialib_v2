from .definitions import Image
from image_processing.config import proxy_at_tmp
from image_processing.core.transforms import color, resize
from pathlib import Path
import pyvips
import tempfile


class ProxyFile:
    def __init__(
        self,
        source_image: Image,
        source_file: Path,
        target_size: tuple[int, int],
        as_scRGB: bool = True,
    ):
        print("generating proxy file")
        file_name = source_file.with_suffix(".proxy.vips")
        if proxy_at_tmp:
            with tempfile.NamedTemporaryFile(
                suffix=".proxy.vips", delete=False
            ) as tmp:
                self.proxy_file_path = Path(tmp.name)
        else:
            self.proxy_file_path = file_name
        img = source_image
        if (
            source_image.interpretation != pyvips.enums.Interpretation.SCRGB
            and as_scRGB
        ):
            img = color.upcast_and_linearise(source_image)
        proxy_image = resize.downscale(img, target_size)
        proxy_image.vipssave(str(self.proxy_file_path))
        self.image = Image.new_from_file(str(self.proxy_file_path))

    def close(self):
        if hasattr(self, "image") and self.image is not None:
            self.image = None

        if hasattr(self, "proxy_file_path") and self.proxy_file_path.exists():
            try:
                self.proxy_file_path.unlink(missing_ok=True)
                print(f"cleaned up: {self.proxy_file_path.name}")
            except OSError:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()
