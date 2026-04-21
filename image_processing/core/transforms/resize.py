from image_processing.core.libvips.definitions import Image
import pyvips


def downscale(
    img: Image,
    target_size: tuple[int, int],
    kernel=pyvips.enums.Kernel.LANCZOS3,
) -> Image:
    target_width, target_height = target_size
    source_width = img.width
    source_height = img.height

    if source_width < target_width and source_height < target_height:
        return img

    source_aspect_ratio = source_width / source_height
    target_aspect_ratio = target_width / target_height

    scale_ratio: float = 1.0

    if target_aspect_ratio >= source_aspect_ratio:
        scale_ratio = target_height / source_height
    else:
        scale_ratio = target_width / source_width

    if scale_ratio == 1.0:
        return img

    return img.resize(scale_ratio, kernel=kernel)
