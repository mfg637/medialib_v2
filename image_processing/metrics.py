from skimage.metrics import peak_signal_noise_ratio
from skimage.metrics import structural_similarity
from skimage.metrics import mean_squared_error
import numpy
import PIL.Image
import typing
from image_processing.libvips.definitions import Image
from image_processing.transforms.compositing import alpha_compose_vips
from image_processing.transforms.color import upcast_and_linearise


DATA_RANGES: dict[numpy.dtype, float] = {
    numpy.dtype(numpy.uint8): float(2**8 - 1),
    numpy.dtype(numpy.uint16): float(2**16 - 1),
    numpy.dtype(numpy.float64): 1.0,
    numpy.dtype(numpy.float32): 1.0,
}


def check_dtypes_equal(metrics_calc):
    def perform_dtype_check(
        image_true: numpy.ndarray, image_test: numpy.ndarray
    ):
        if image_true.dtype == image_test.dtype:
            return metrics_calc(image_true, image_test)
        else:
            raise TypeError(
                "dtypes of image_true and image_test must be the same"
            )

    return perform_dtype_check


@check_dtypes_equal
def calc_rmse(image_true: numpy.ndarray, image_test: numpy.ndarray) -> float:
    mse = mean_squared_error(image_true, image_test)
    return numpy.sqrt(mse)


@check_dtypes_equal
def calc_psnr(image_true: numpy.ndarray, image_test: numpy.ndarray) -> float:
    return peak_signal_noise_ratio(
        image_true, image_test, data_range=DATA_RANGES[image_true.dtype]
    )


def rgb_to_luma(img: numpy.ndarray) -> numpy.ndarray:
    return 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]


@check_dtypes_equal
def calc_ssim(image_true: numpy.ndarray, image_test: numpy.ndarray) -> float:
    luma_true = rgb_to_luma(image_true)
    luma_test = rgb_to_luma(image_test)

    max_val = max(luma_true.max(), luma_test.max())
    min_val = min(luma_true.min(), luma_test.min())

    luma_true = (luma_true - min_val) / (max_val - min_val)
    luma_test = (luma_test - min_val) / (max_val - min_val)

    return structural_similarity(
        luma_true,
        luma_test,
        data_range=1.0,
        gaussian_weights=True,
        use_sample_covariance=True,
    )  # pyright: ignore[reportReturnType]


image_type = typing.Union[PIL.Image.Image, Image, numpy.ndarray]


def normalize_for_metrics(img: Image) -> Image:
    if img.hasalpha():
        return upcast_and_linearise(alpha_compose_vips(img))
    else:
        return upcast_and_linearise(img)


def normalize_for_metrics_srgb(img: Image) -> Image:
    if img.hasalpha():
        return alpha_compose_vips(img).colourspace("srgb")
    else:
        return img.colourspace("srgb")


def image_to_ndarray(image: image_type):
    if isinstance(image, numpy.ndarray):
        return image
    elif isinstance(image, Image):
        return image.numpy()
    else:
        return numpy.array(image)


def debug_ndarray(**kwargs: numpy.ndarray) -> None:
    if len(kwargs) != 1:
        raise ValueError(
            "Function vips_image_debug expects exactly one named argument"
        )

    name, value = next(iter(kwargs.items()))

    if not isinstance(value, numpy.ndarray):
        raise TypeError(
            (
                f"Argument {name} expected to be "
                f"numpy.ndarray, "
                f"not {type(value)}"
            )
        )

    print(f"{name}: dtype: {value.dtype}, height: {value.shape}")
    print(f"{name}: min: {value.min()}, max: {value.max()}")
    print(f"{name}: average: {numpy.average(value)}, deviation: {value.std()}")


def calc_metrics(image_true: image_type, image_test: image_type):
    image_true_array = image_to_ndarray(image_true)
    image_test_array = image_to_ndarray(image_test)

    metrics: dict[str, float] = {}

    metrics["rmse"] = calc_rmse(image_true_array, image_test_array)
    metrics["psnr"] = calc_psnr(image_true_array, image_test_array)

    return metrics
