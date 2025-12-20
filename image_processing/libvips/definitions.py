import typing
from typing import Optional
import pyvips


Interpretation = typing.Union[str, pyvips.enums.Interpretation]
BandFormat = typing.Union[str, pyvips.enums.BandFormat]
Kernel = typing.Union[str, pyvips.enums.Kernel]
HeifCodec = typing.Union[str, pyvips.enums.ForeignHeifCompression]
HeifEncoder = typing.Union[str, pyvips.enums.ForeignHeifEncoder]


class Image(pyvips.Image):
    @staticmethod
    def new_from_file(vips_filename: str, **kwargs) -> "Image":
        return pyvips.Image.new_from_file(
            vips_filename, **kwargs
        )  # pyright: ignore[reportReturnType]

    @property
    def width(self) -> int:
        """Image width in pixels."""
        return super().width  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def height(self) -> int:
        """Image height in pixels."""
        return super().height  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def bands(self) -> int:
        """Number of bands in image."""
        return super().bands  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def interpretation(self) -> Interpretation:
        """Suggested interpretation of image pixel values."""
        return (
            super().interpretation  # pyright: ignore[reportAttributeAccessIssue]
        )

    @property
    def format(self) -> BandFormat:
        """The format used for each band element."""
        return super().format()  # pyright: ignore[reportAttributeAccessIssue]

    def colourspace(
        self,
        space: Interpretation,
        *,
        source_space: Optional[Interpretation] = None,
    ) -> "Image":
        if source_space is not None:
            return super().colourspace(  # pyright: ignore[reportAttributeAccessIssue]
                space, source_space=source_space
            )
        return (
            super().colourspace(  # pyright: ignore[reportAttributeAccessIssue]
                space
            )
        )

    def cast(self, fmt: BandFormat) -> "Image":
        return super().cast(fmt)  # pyright: ignore[reportAttributeAccessIssue]

    def write_to_file(self, path: str, **kwargs) -> None:
        super().write_to_file(
            path, **kwargs
        )  # pyright: ignore[reportAttributeAccessIssue]

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
        super().pngsave(  # pyright: ignore[reportAttributeAccessIssue]
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
        return super().resize(  # pyright: ignore[reportAttributeAccessIssue]
            scale, **kwargs
        )

    def linear(self, a: float, b: float, uchar: bool = False) -> "Image":
        return super().linear(  # pyright: ignore[reportAttributeAccessIssue]
            a, b, uchar
        )

    def scRGB2sRGB(self, depth: int = 8) -> "Image":
        return (
            super().scRGB2sRGB(  # pyright: ignore[reportAttributeAccessIssue]
                depth
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
        super().heifsave(  # pyright: ignore[reportAttributeAccessIssue]
            filename, **kwargs
        )

    def webpsave(
        self, filename: str, *, Q: int = 75, effort: int = 4, **kwargs
    ) -> "Image":
        kwargs["Q"] = Q
        kwargs["effort"] = effort
        return super().webpsave(  # pyright: ignore[reportAttributeAccessIssue]
            filename, **kwargs
        )

    def extract_band(self, band: int, n: int = 1) -> Image:
        return super().extract_band(  # pyright: ignore[reportAttributeAccessIssue]
            band, n
        )
