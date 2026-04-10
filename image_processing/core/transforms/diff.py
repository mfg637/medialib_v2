from image_processing.core.libvips.definitions import Image
from image_processing.core.utils import debug_ndarray
import numpy as np


def generate_diff_heatmap(image_1: Image, image_2: Image) -> np.ndarray:
    if image_1.width != image_2.width or image_1.height != image_2.height:
        raise ValueError(
            (
                "Unable to compare images: different sizes: "
                f"{image_1.width}x{image_1.height} not equal to "
                f"{image_2.width}x{image_2.height}"
            )
        )

    image_1 = image_1.colourspace("srgb")
    image_2 = image_2.colourspace("srgb")

    diff_array = (image_1 - image_2).abs().numpy()

    combined_diff = np.sum(diff_array, axis=-1, dtype=np.uint16)

    debug_ndarray(combined_diff=combined_diff)
    return combined_diff


def generate_diff_heatmap_as_8bit_image(
    image_1: Image, image_2: Image
) -> Image:
    heatmap_array = generate_diff_heatmap(image_1, image_2)
    clipped_8bit = np.clip(heatmap_array, 0, 255).astype(np.uint8)
    return Image.new_from_array(clipped_8bit)
