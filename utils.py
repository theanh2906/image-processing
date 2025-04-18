from typing import Tuple

import imageio.v3 as iio
import matplotlib.pyplot as plt
import numpy as np


def save_image(image, output_path):
    """
    Save an image to the specified file path.

    Parameters:
        image (numpy.ndarray): The image to save.
        output_path (str): The file path where the image will be saved.

    Returns:
        None
    """
    success = iio.imwrite(output_path, image, plugin='tifffile')
    if success:
        print(f"Image successfully saved to {output_path}")
    else:
        print(f"Error: Unable to save the image to {output_path}")


def display_comparison(original: np.ndarray, processed: np.ndarray,
                       original_title: str, processed_title: str, subplot_figsize: Tuple[int, int] = (12, 6)) -> None:
    """Display original and processed images side by side."""
    plt.figure(figsize=subplot_figsize)

    plt.subplot(1, 2, 1)
    plt.title(original_title)
    plt.imshow(original)
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.title(processed_title)
    plt.imshow(processed)
    plt.axis('off')

    plt.show()
