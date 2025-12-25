import typing
from collections.abc import Sequence, Buffer
from typing import Optional
import pyvips
import warnings
import numpy


Interpretation = typing.Union[str, pyvips.enums.Interpretation]
BandFormat = typing.Union[str, pyvips.enums.BandFormat]
Kernel = typing.Union[str, pyvips.enums.Kernel]
HeifCodec = typing.Union[str, pyvips.enums.ForeignHeifCompression]
HeifEncoder = typing.Union[str, pyvips.enums.ForeignHeifEncoder]
BackgroundColor = typing.Union[float, Sequence[float]]
pyvips.BlendMode = typing.Union[str, pyvips.enums.BlendMode]
Coding = typing.Union[str, pyvips.enums.Coding]


class Image:
    __slots__ = ("_img",)

    def __init__(self, img: pyvips.Image):
        self._img: pyvips.Image = img

    @staticmethod
    def new_from_file(vips_filename: str, **kwargs) -> "Image":
        return Image(
            pyvips.Image.new_from_file(  # pyright: ignore[reportArgumentType]
                vips_filename, **kwargs
            )
        )

    @staticmethod
    def new_from_array(
        obj,
        scale: float = 1.0,
        offset: float = 0.0,
        interpretation: Optional[Interpretation] = None,
    ) -> Image:
        kwargs = dict()
        kwargs["offset"] = offset
        kwargs["scale"] = scale
        if interpretation is not None:
            kwargs["interpretation"] = interpretation
        return Image(pyvips.Image.new_from_array(obj, **kwargs))

    @staticmethod
    def new_from_buffer(data: Buffer, options: str = "", **kwargs):
        return Image(
            pyvips.Image.new_from_buffer(
                data, options, **kwargs
            )  # pyright: ignore[reportArgumentType]
        )

    @staticmethod
    def new_from_memory(
        data: bytes, width: int, height: int, bands: int, _format: BandFormat
    ) -> Image:
        return Image(
            pyvips.Image.new_from_memory(data, width, height, bands, _format)
        )

    def new_from_image(self, value: BackgroundColor):
        return Image(self._img.new_from_image(value))

    @property
    def width(self) -> int:
        """Image width in pixels."""
        return self._img.width  # pyright: ignore[reportReturnType]

    @property
    def height(self) -> int:
        """Image height in pixels."""
        return self._img.height  # pyright: ignore[reportReturnType]

    @property
    def bands(self) -> int:
        """Number of bands in image."""
        return self._img.bands  # pyright: ignore[reportReturnType]

    @property
    def interpretation(self) -> Interpretation:
        """Suggested interpretation of image pixel values."""
        return self._img.interpretation  # pyright: ignore[reportReturnType]

    @property
    def format(self) -> BandFormat:
        """The format used for each band element."""
        return self._img.format  # pyright: ignore[reportReturnType]

    def colourspace(
        self,
        space: Interpretation,
        *,
        source_space: Optional[Interpretation] = None,
    ) -> "Image":
        if source_space is not None:
            return Image(
                self._img.colourspace(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                    space,
                    source_space=source_space,  # # pyright: ignore[reportCallIssue]
                )
            )
        return Image(
            self._img.colourspace(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                space
            )
        )

    def cast(self, fmt: BandFormat) -> "Image":
        return Image(
            self._img.cast(
                fmt
            )  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
        )

    def write_to_file(self, path: str, **kwargs) -> None:
        self._img.write_to_file(path, **kwargs)

    def pngsave(
        self,
        filename: str,
        *,
        compression: int = 6,
        bitdepth: Optional[int] = None,
        **kwargs,
    ) -> None:
        kwargs["compression"] = compression
        if bitdepth is not None:
            kwargs["bitdepth"] = bitdepth
        self._img.pngsave(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
            filename, **kwargs
        )

    def resize(
        self,
        scale: float,
        *,
        kernel: Kernel = pyvips.enums.Kernel.LANCZOS3,
        gap: float = 2.0,
        vscale: Optional[float] = None,
    ) -> "Image":
        kwargs = dict()
        kwargs["kernel"] = kernel
        kwargs["gap"] = gap
        if vscale is not None:
            kwargs["vscale"] = vscale
        return Image(
            self._img.resize(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                scale, **kwargs
            )
        )

    def linear(self, a: float, b: float, uchar: bool = False) -> "Image":
        return Image(
            self._img.linear(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                a, b, uchar=uchar  # pyright: ignore[reportCallIssue]
            )
        )

    def scRGB2sRGB(self, depth: int = 8) -> "Image":
        return Image(
            self._img.scRGB2sRGB(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                depth=depth  # pyright: ignore[reportCallIssue]
            )
        )

    def heifsave(
        self,
        filename: str,
        *,
        compression: Optional[HeifCodec] = None,
        encoder: Optional[HeifEncoder] = None,
        Q: Optional[int] = None,
        bitdepth: Optional[int] = None,
        effort: Optional[int] = None,
        **kwargs,
    ) -> None:
        if compression is not None:
            kwargs["compression"] = compression
        if encoder is not None:
            kwargs["encoder"] = encoder
        if Q is not None:
            kwargs["Q"] = Q
        if bitdepth is not None:
            kwargs["bitdepth"] = bitdepth
        if effort is not None:
            kwargs["effort"] = effort
        self._img.heifsave(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
            filename, **kwargs
        )

    def webpsave(
        self, filename: str, *, Q: int = 75, effort: int = 4, **kwargs
    ) -> "Image":
        kwargs["Q"] = Q
        kwargs["effort"] = effort
        return Image(
            self._img.webpsave(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                filename, **kwargs
            )
        )

    def extract_band(self, band: int, n: int = 1) -> Image:
        return Image(
            self._img.extract_band(  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
                band, n=n  # pyright: ignore[reportCallIssue]
            )
        )

    def numpy(self, dtype: Optional[numpy.dtype] = None) -> numpy.ndarray:
        return self._img.numpy(dtype)

    def hasalpha(self) -> bool:
        value = self._img.hasalpha()
        if value not in {0, 1}:
            raise Exception(
                f"pyvips.Image.hasalpha() return unexpected value {value}"
            )
        return bool(value)

    def bandjoin(self, other) -> Image:
        return Image(
            self._img.bandjoin(
                other._img
            )  # pyright: ignore[reportArgumentType]
        )

    def composite2(
        self,
        overlay: Image,
        mode: pyvips.BlendMode,
        x: Optional[int] = None,
        y: Optional[int] = None,
        compositing_space: Optional[Interpretation] = None,
        premultiplied: Optional[bool] = None,
    ) -> Image:
        kwargs = dict()
        if x is not None:
            kwargs["x"] = x
        if y is not None:
            kwargs["y"] = y
        if compositing_space is not None:
            kwargs["compositing_space"] = compositing_space
        if premultiplied is not None:
            kwargs["premultiplied"] = premultiplied
        return Image(
            self._img.composite2(
                overlay._img, mode, **kwargs
            )  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
        )

    def flatten(
        self,
        background: Optional[list[float]] = None,
        max_alpha: Optional[float] = None,
    ) -> Image:
        kwargs = dict()
        if background is not None:
            kwargs["background"] = background
        if max_alpha is not None:
            kwargs["max_alpha"] = max_alpha
        return Image(
            self._img.flatten(
                **kwargs
            )  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
        )

    def copy(
        self,
        *,
        width: Optional[int] = None,
        height: Optional[int] = None,
        bands: Optional[int] = None,
        _format: Optional[BandFormat] = None,
        coding: Optional[Coding] = None,
        interpretation: Optional[Interpretation] = None,
        xres: Optional[float] = None,
        yres: Optional[float] = None,
        xoffset: Optional[int] = None,
        yoffset: Optional[int] = None,
    ) -> Image:
        """Copy an image, optionally modifying the header.
        VIPS copies images by copying pointers, so this operation is instant,
        even for very large images.

        You can optionally change any or all header fields during the copy.
        You can make any change which does not change the size of a pel,
        so for example you can turn a 4-band uchar image into
        a 2-band ushort image, but you cannot change a 100 x 100 RGB image
        into a 300 x 100 mono image.
        """
        kwargs = dict()
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        if bands is not None:
            kwargs["bands"] = bands
        if _format is not None:
            kwargs["format"] = _format
        if coding is not None:
            kwargs["coding"] = coding
        if interpretation is not None:
            kwargs["interpretation"] = interpretation
        if xres is not None:
            kwargs["xres"] = xres
        if yres is not None:
            kwargs["y_res"] = yres
        if xoffset is not None:
            kwargs["xoffset"] = xoffset
        if yoffset is not None:
            kwargs["yoffset"] = yoffset
        return Image(
            self._img.copy(
                **kwargs
            )  # pyright: ignore[reportCallIssue, reportArgumentType, reportOptionalCall]
        )

    def close(self):
        warnings.warn(
            "Image.close() is a temporary no-op for pyvips.Image. "
            "Remove this call when Pillow dependency is eliminated.",
            category=DeprecationWarning,
            stacklevel=2,
        )
