# Image Processing

A comprehensive Python package for image processing with edge detection, sharpening, and filtering capabilities.

## Features

- **Edge Detection**: Detect edges in images using the Canny edge detection algorithm
  - Customizable parameters (blur, high/low thresholds)
  - Complete implementation of the Canny algorithm
- **Image Sharpening**: Sharpen images using various methods:
  - Unsharp Mask
  - OpenCV kernel-based sharpening
  - TensorFlow-based sharpening
- **Image Filtering**: Apply various PIL filters to images:
  - Blur, Contour, Detail
  - Edge Enhancement, Edge Enhancement More
  - Emboss, Find Edges
  - Sharpen, Smooth, Smooth More
  - Gaussian Blur
- **Interactive Mode**: User-friendly menu-driven interface for processing images

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/image-processing.git
cd image-processing

# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/MacOS

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

The package provides a command-line interface for easy access to all functionality:

```bash
# Run the demo (displays all capabilities)
python main.py

# Run the interactive menu
python main.py --interactive

# Edge detection
python main.py --input images/image.jpg --output output/edges.jpg edge

# Edge detection with custom parameters
python main.py --input images/image.jpg --output output/edges.jpg edge --blur 1.5 --high-threshold 100 --low-threshold 50

# Image sharpening
python main.py --input images/image.jpg --output output/sharp.jpg sharpen --method unsharp_mask

# Image sharpening with custom parameters
python main.py --input images/image.jpg --output output/sharp.jpg sharpen --method tensorflow --blur-kernel-size 5 --sharpening-amount 2.0

# Apply a filter
python main.py --input images/image.jpg --output output/filtered.jpg filter --filter-name find_edges
```

### Python API

You can also use the package as a Python API:

```python
from edge_detection import detect_edges, canny_edge_detector
from sharpening import sharpen_image, apply_unsharp_mask, sharpen_with_cv2, sharpen_with_tensorflow
from filters import apply_pil_filters, apply_single_filter
from image_utils import load_image, save_image, display_comparison, display_multiple_images

# Edge detection with default parameters
detect_edges(
    "images/image.jpg",
    output_path="output/edges.jpg",
    method="canny"
)

# Edge detection with custom parameters
detect_edges(
    "images/image.jpg",
    output_path="output/edges_custom.jpg",
    method="canny",
    blur=1.5,
    high_threshold=100,
    low_threshold=50,
    display_result=True
)

# Image sharpening with default parameters
sharpen_image(
    "images/image.jpg",
    output_path="output/sharp.jpg",
    method="unsharp_mask"
)

# Image sharpening with custom parameters
sharpen_image(
    "images/image.jpg",
    output_path="output/sharp_custom.jpg",
    method="tensorflow",
    blur_kernel_size=5,
    sharpening_amount=2.0,
    display_result=True
)

# Apply a specific filter
apply_single_filter(
    "images/image.jpg",
    filter_name="find_edges",
    output_path="output/filtered.jpg",
    display_result=True
)

# Apply all filters and display them
filtered_images = apply_pil_filters("images/image.jpg")

# Utility functions for working with images
image = load_image("images/image.jpg")
processed_image = canny_edge_detector(image)
save_image(processed_image, "output/processed.jpg")
display_comparison(image, processed_image, "Original", "Processed")
```

## Module Structure

- `main.py`: Main entry point, CLI, and interactive menu interface
- `image_utils.py`: Utility functions for image loading, saving, and display
- `edge_detection.py`: Edge detection algorithms implementation
- `canny_edge_detector.py`: Specialized implementation of Canny edge detection
- `sharpening.py`: Image sharpening algorithms (Unsharp Mask, OpenCV, TensorFlow)
- `unsharp_mark_kernel.py`: Kernel implementation for unsharp mask algorithm
- `filters.py`: PIL filter application and management
- `image_processing.py`: Core image processing functionality
- `utils.py`: General utility functions for the package

## Dependencies

- OpenCV
- NumPy
- Matplotlib
- Pillow (PIL)
- TensorFlow
- SciPy
- imageio

## License

MIT
