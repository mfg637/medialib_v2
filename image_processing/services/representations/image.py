from base.shared_enums.medialib_model import RepresentationTypeEnum
from image_processing.core.transforms.resize import downscale
from image_processing.core.encoders import avif, webp
from image_processing.core.libvips.definitions import Image
from image_processing.core.libvips.proxy_file import ProxyFile
from image_processing.core.transforms.color import (
    upcast_and_linearise,
    to_LAB_as_pillow_bands,
)
from image_processing.core.transforms.compositing import alpha_compose_vips
from image_processing.core.specification.image import (
    get_image_compatibility_level,
    FORMAT_LEVEL,
)
from base.shared_knowledge.file_format import FormatEnum
from image_processing.core.matrix_scan import zigzag_scan
from image_processing.core.utils import bit_round
from .common import Representation
from image_processing.services.media_passport import StaticImagePassport
from typing import Callable, Optional
from PIL import Image as PIL_Image

import abc
import enum
import pathlib
import imagehash
import dataclasses
import numpy as np


def save_img_4096(
    csRGB_image: Image, source_file: pathlib.Path
) -> Representation:
    output_file = source_file.with_stem(
        f"{source_file.stem} 4096"
    ).with_suffix(".avif")
    avif.encode(csRGB_image, output_file, quality=85)
    width = csRGB_image.width
    height = csRGB_image.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.AVIF),
        output_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.AVIF,
    )


def save_img_2048(
    csRGB_image: Image, source_file: pathlib.Path
) -> Representation:
    output_file = source_file.with_stem(
        f"{source_file.stem} 2048"
    ).with_suffix(".avif")
    avif.encode(csRGB_image, output_file, quality=90, effort=3)
    width = csRGB_image.width
    height = csRGB_image.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.AVIF),
        output_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.AVIF,
    )


def save_img_1024(
    csRGB_image: Image, source_file: pathlib.Path
) -> Representation:
    output_file = source_file.with_stem(
        f"{source_file.stem} 1024"
    ).with_suffix(".webp")
    webp.encode(
        csRGB_image,
        output_file,
        quality=95,
        smart_subsample=True,
        smart_deblock=True,
        effort=5,
    )
    width = csRGB_image.width
    height = csRGB_image.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.WEBP),
        output_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.WEBP,
    )


def save_img_512(
    csRGB_image: Image, source_file: pathlib.Path
) -> Representation:
    output_file = source_file.with_stem(f"{source_file.stem} 512").with_suffix(
        ".webp"
    )
    webp.encode(csRGB_image, output_file, quality=90, smart_deblock=True)
    width = csRGB_image.width
    height = csRGB_image.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.WEBP),
        output_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.WEBP,
    )


def save_img_256(
    csRGB_image: Image, source_file: pathlib.Path
) -> Representation:
    output_file = source_file.with_stem(f"{source_file.stem} 256").with_suffix(
        ".webp"
    )
    webp.encode(csRGB_image, output_file, quality=85, alpha_q=95)
    width = csRGB_image.width
    height = csRGB_image.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.WEBP),
        output_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.WEBP,
    )


def save_img_128(
    csRGB_image: Image, source_file: pathlib.Path
) -> Representation:
    output_file = source_file.with_stem(f"{source_file.stem} 128").with_suffix(
        ".webp"
    )
    webp.encode(csRGB_image, output_file, quality=80, alpha_q=90)
    width = csRGB_image.width
    height = csRGB_image.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.WEBP),
        output_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.WEBP,
    )


saver_function_type = Callable[[Image, pathlib.Path], Representation]


IMAGE_REPRESENTATION_SAVERS: dict[int, saver_function_type] = {
    4096: save_img_4096,
    2048: save_img_2048,
    1024: save_img_1024,
    512: save_img_512,
    256: save_img_256,
    128: save_img_128,
}


def save_img_jpeg(img: Image, source_file: pathlib.Path) -> Representation:
    width = img.width
    height = img.height
    return Representation(
        get_image_compatibility_level((width, height), FormatEnum.JPEG),
        source_file,
        width,
        height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.JPEG,
    )


def save_img_svg(img: Image, source_file: pathlib.Path) -> Representation:
    return Representation(
        FORMAT_LEVEL[FormatEnum.SVG],
        source_file,
        img.width,
        img.height,
        RepresentationTypeEnum.IMAGE,
        FormatEnum.SVG,
    )


class ProcessingCases(enum.Enum):
    LARGER = enum.auto()
    SIMILAR = enum.auto()
    SMALL = enum.auto()


class BaseRepresentationStrategy(abc.ABC):
    PROCESSING_ORDER = [128, 256, 512, 1024, 2048, 4096]

    def __init__(self, proxy_threshold: int = 4096):
        self.proxy_threshold = proxy_threshold

    def _prepare_image_data(
        self, source_file: pathlib.Path
    ) -> tuple[Image, int, int, Optional[ProxyFile]]:
        source_img = Image.new_from_file(str(source_file))
        width = source_img.width
        height = source_img.height
        proxy_file: Optional[ProxyFile] = None
        if width > self.proxy_threshold or height > self.proxy_threshold:
            proxy_file = ProxyFile(
                source_img,
                source_file,
                (self.proxy_threshold, self.proxy_threshold),
            )
            upcasted = proxy_file.image
            if upcasted is None:
                raise Exception("Error while creating proxy image")
        else:
            upcasted = upcast_and_linearise(source_img)

        return upcasted, width, height, proxy_file

    def make_representations(
        self, source_file: pathlib.Path
    ) -> list[Representation]:
        upcasted, width, height, proxy_file = self._prepare_image_data(
            source_file
        )
        representations = []

        for index, size in enumerate(self.PROCESSING_ORDER):
            _case = self._detect_processing_case(size, width, height, index)
            if _case is ProcessingCases.SMALL:
                break
            print("processing representation", size)
            processed_img = self.process_image(size, _case, upcasted)
            saver = self.get_saver(size, _case)
            representations.append(saver(processed_img, source_file))

        representations.extend(self.post_process(upcasted, source_file))

        if proxy_file is not None:
            proxy_file.close()

        return representations

    @abc.abstractmethod
    def get_saver(
        self, size: int, _case: ProcessingCases
    ) -> saver_function_type:
        """Returns saver function for concrete size."""
        pass

    def process_image(
        self, size_limit: int, _case: ProcessingCases, prepared_image: Image
    ) -> Image:
        if _case is ProcessingCases.LARGER:
            return downscale(prepared_image, (size_limit, size_limit))
        else:
            return prepared_image

    def _detect_processing_case(
        self,
        size_limit: int,
        source_width: int,
        source_height: int,
        index: int,
    ) -> ProcessingCases:
        if source_width > size_limit or source_height > size_limit:
            return ProcessingCases.LARGER
        if index > 0:
            prev_size = self.PROCESSING_ORDER[index - 1]
            if source_width > prev_size or source_height > prev_size:
                return ProcessingCases.SIMILAR
            else:
                return ProcessingCases.SMALL
        return ProcessingCases.SIMILAR

    def post_process(
        self, img: Image, path: pathlib.Path
    ) -> list[Representation]:
        return []


class DefaultRepresentationStrategy(BaseRepresentationStrategy):
    def get_saver(
        self, size: int, _case: ProcessingCases
    ) -> saver_function_type:
        return IMAGE_REPRESENTATION_SAVERS[size]


class JPEG_RepresentationStrategy(BaseRepresentationStrategy):
    def get_saver(
        self, size: int, _case: ProcessingCases
    ) -> saver_function_type:
        if _case is ProcessingCases.LARGER:
            return IMAGE_REPRESENTATION_SAVERS[size]
        else:
            return save_img_jpeg


class SVG_RepresentationStrategy(BaseRepresentationStrategy):
    PROCESSING_ORDER = [128, 256, 512, 1024, 2048]

    def __init__(self):
        super().__init__(proxy_threshold=2048)

    def get_saver(
        self, size: int, _case: ProcessingCases
    ) -> saver_function_type:
        return IMAGE_REPRESENTATION_SAVERS[size]

    def post_process(
        self, img: Image, path: pathlib.Path
    ) -> list[Representation]:
        return [save_img_svg(img, path)]


class VideoThumbnailRepresentationStrategy(BaseRepresentationStrategy):
    def __init__(self, thumbnail_image: Image, proxy_threshold: int = 4096):
        super().__init__(proxy_threshold)
        self.thumbnail_image = thumbnail_image

    def _prepare_image_data(
        self, source_file: pathlib.Path
    ) -> tuple[Image, int, int, Optional[ProxyFile]]:
        source_img = self.thumbnail_image
        width = source_img.width
        height = source_img.height
        proxy_file: Optional[ProxyFile] = None
        if width > self.proxy_threshold or height > self.proxy_threshold:
            proxy_file = ProxyFile(
                source_img,
                source_file,
                (self.proxy_threshold, self.proxy_threshold),
            )
            upcasted = proxy_file.image
            if upcasted is None:
                raise Exception("Error while creating proxy image")
        else:
            upcasted = upcast_and_linearise(source_img)

        return upcasted, width, height, proxy_file

    def get_saver(
        self, size: int, _case: ProcessingCases
    ) -> saver_function_type:
        return IMAGE_REPRESENTATION_SAVERS[size]


def calculate_visual_hash(p_img: PIL_Image.Image, hash_size: int) -> bytes:
    hash_obj = imagehash.phash(p_img, hash_size=hash_size)
    ordered_bits = zigzag_scan(hash_obj.hash)
    packed_bytes = np.packbits(ordered_bits).tobytes()
    return packed_bytes


@dataclasses.dataclass
class ImageHash:
    aspect_ratio: float
    l_hash: bytes
    a_hash: bytes
    b_hash: bytes


def get_image_signatures(passport: StaticImagePassport) -> ImageHash:
    aspect_ratio_approximate = bit_round(
        passport.width / passport.height, precision=8
    )
    image = passport.image
    if image.hasalpha():
        image = alpha_compose_vips(image)
    with ProxyFile(
        passport.image,
        passport.source_file,
        target_size=(1024, 1024),
        as_scRGB=False,
    ) as proxy:
        if proxy.image is None:
            raise ValueError("Proxy image is not exists")
        p_L, p_A, p_B = to_LAB_as_pillow_bands(proxy.image)

        l_hash = calculate_visual_hash(p_L, hash_size=16)
        a_hash = calculate_visual_hash(p_A, hash_size=8)
        b_hash = calculate_visual_hash(p_B, hash_size=8)
        return ImageHash(aspect_ratio_approximate, l_hash, a_hash, b_hash)
