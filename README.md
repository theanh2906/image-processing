# Image Processing

A comprehensive Python package for image processing with edge detection, sharpening, and filtering capabilities.

## Features

- **Edge Detection**: Detect edges in images using the Canny edge detection algorithm
- **Image Sharpening**: Sharpen images using various methods:
  - Unsharp Mask
  - OpenCV kernel-based sharpening
  - TensorFlow-based sharpening
- **Image Filtering**: Apply various PIL filters to images:
  - Blur, Contour, Detail
  - Edge Enhancement
  - Emboss, Find Edges
  - Sharpen, Smooth
  - Gaussian Blur

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

# Edge detection
python main.py --input images/image.jpg --output output/edges.jpg edge

# Image sharpening
python main.py --input images/image.jpg --output output/sharp.jpg sharpen --method unsharp_mask

# Apply a filter
python main.py --input images/image.jpg --output output/filtered.jpg filter --filter-name find_edges
```

### Python API

You can also use the package as a Python API:

```python
from edge_detection import detect_edges
from sharpening import sharpen_image
from filters import apply_pil_filters, apply_single_filter

# Edge detection
detect_edges(
    "images/image.jpg",
    output_path="output/edges.jpg",
    method="canny"
)

# Image sharpening
sharpen_image(
    "images/image.jpg",
    output_path="output/sharp.jpg",
    method="unsharp_mask"
)

# Apply a filter
apply_single_filter(
    "images/image.jpg",
    filter_name="find_edges",
    output_path="output/filtered.jpg"
)

# Apply all filters and display them
apply_pil_filters("images/image.jpg")
```

## Module Structure

- `main.py`: Main entry point and CLI
- `image_utils.py`: Utility functions for image loading, saving, and display
- `edge_detection.py`: Edge detection algorithms
- `sharpening.py`: Image sharpening algorithms
- `filters.py`: PIL filter application

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