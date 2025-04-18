"""
Main entry point for the image processing application.

This module demonstrates the various image processing capabilities
provided by the package.
"""

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import argparse
from typing import List, Optional

from image_utils import load_image, save_image, display_comparison, display_multiple_images
from edge_detection import detect_edges
from sharpening import sharpen_image
from filters import apply_pil_filters, apply_single_filter


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Image Processing Tool")

    # Main arguments
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Path to the input image")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Path to save the output image")
    parser.add_argument("--no-display", action="store_true",
                        help="Don't display the processed images")

    # Processing type
    subparsers = parser.add_subparsers(dest="command", help="Processing command")

    # Edge detection
    edge_parser = subparsers.add_parser("edge", help="Edge detection")
    edge_parser.add_argument("--method", type=str, default="canny",
                            choices=["canny"],
                            help="Edge detection method")
    edge_parser.add_argument("--blur", type=float, default=1.0,
                            help="Gaussian blur sigma value")
    edge_parser.add_argument("--high-threshold", type=int, default=91,
                            help="High threshold for edge detection")
    edge_parser.add_argument("--low-threshold", type=int, default=31,
                            help="Low threshold for edge detection")

    # Sharpening
    sharpen_parser = subparsers.add_parser("sharpen", help="Image sharpening")
    sharpen_parser.add_argument("--method", type=str, default="unsharp_mask",
                               choices=["unsharp_mask", "cv2", "tensorflow"],
                               help="Sharpening method")
    sharpen_parser.add_argument("--blur-kernel-size", type=int, default=7,
                               help="Size of Gaussian blur kernel for unsharp mask")
    sharpen_parser.add_argument("--sharpening-amount", type=float, default=1.5,
                               help="Intensity of sharpening effect for unsharp mask")
    sharpen_parser.add_argument("--threshold", type=int, default=10,
                               help="Minimum difference for sharpening to reduce noise")

    # Filtering
    filter_parser = subparsers.add_parser("filter", help="Apply PIL filters")
    filter_parser.add_argument("--filter-name", type=str, default=None,
                              help="Name of the filter to apply (if not specified, all filters will be applied)")

    return parser.parse_args()


def ensure_output_path(output_path: Optional[str], input_path: str, command: str) -> str:
    """Ensure that an output path exists."""
    if output_path:
        return output_path

    # Create a default output path in the output directory
    os.makedirs("output", exist_ok=True)
    input_filename = os.path.basename(input_path)
    name, ext = os.path.splitext(input_filename)

    return os.path.join("output", f"{name}_{command}{ext}")


def main():
    """Main entry point."""
    args = parse_args()

    # Ensure the input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return

    # Process based on the command
    if args.command == "edge":
        # Edge detection
        output_path = ensure_output_path(args.output, args.input, "edge")
        detect_edges(
            args.input,
            output_path=output_path,
            method=args.method,
            blur=args.blur,
            high_threshold=args.high_threshold,
            low_threshold=args.low_threshold,
            display_result=not args.no_display
        )
        print(f"Edge detection completed. Output saved to {output_path}")

    elif args.command == "sharpen":
        # Image sharpening
        output_path = ensure_output_path(args.output, args.input, "sharp")
        sharpen_image(
            args.input,
            output_path=output_path,
            method=args.method,
            blur_kernel_size=args.blur_kernel_size,
            sharpening_amount=args.sharpening_amount,
            threshold=args.threshold,
            display_result=not args.no_display
        )
        print(f"Image sharpening completed. Output saved to {output_path}")

    elif args.command == "filter":
        # Apply PIL filters
        if args.filter_name:
            # Apply a single filter
            output_path = ensure_output_path(args.output, args.input, args.filter_name)
            apply_single_filter(
                args.input,
                filter_name=args.filter_name,
                output_path=output_path,
                display_result=not args.no_display
            )
            print(f"Filter '{args.filter_name}' applied. Output saved to {output_path}")
        else:
            # Apply all filters
            apply_pil_filters(
                args.input,
                display_result=not args.no_display
            )
            print("All filters applied and displayed.")
    else:
        print("Please specify a command: edge, sharpen, or filter")


def demo():
    """Run a demonstration of all image processing capabilities."""
    print("Image Processing Demo")
    print("====================")

    # Sample image paths
    sample_image = "images/image.jpg"
    landscape_image = "images/background_landscape.png"

    if not os.path.exists(sample_image) or not os.path.exists(landscape_image):
        print("Error: Sample images not found. Please ensure the images directory exists with sample images.")
        return

    # Create an output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)

    # 1. Edge Detection
    print("\n1. Edge Detection")
    detect_edges(
        landscape_image,
        output_path="output/edges.jpg",
        method="canny",
        blur=1.0,
        high_threshold=91,
        low_threshold=31
    )

    # 2. Image Sharpening
    print("\n2. Image Sharpening")
    # 2.1 Unsharp Mask
    sharpen_image(
        sample_image,
        output_path="output/sharpened_unsharp_mask.jpg",
        method="unsharp_mask"
    )

    # 2.2 OpenCV Sharpening
    sharpen_image(
        sample_image,
        output_path="output/sharpened_cv2.jpg",
        method="cv2"
    )

    # 3. PIL Filters
    print("\n3. PIL Filters")
    # 3.1 Apply a single filter
    apply_single_filter(
        sample_image,
        filter_name="find_edges",
        output_path="output/filter_find_edges.jpg"
    )

    # 3.2 Apply all filters
    apply_pil_filters(sample_image)

    print("\nDemo completed. All processed images saved to the 'output' directory.")


def interactive_menu():
    """Run an interactive menu to select image processing options."""
    print("Image Processing Tool - Interactive Menu")
    print("=======================================")

    while True:
        print("\nSelect an option:")
        print("1. Process an image")
        print("2. Run demo (uses sample images)")
        print("3. Exit")

        main_choice = input("\nEnter your choice (1-3): ")

        if main_choice == '2':
            # Run the demo
            demo()
            continue
        elif main_choice == '3':
            # Exit
            print("Exiting program.")
            break
        elif main_choice != '1':
            print("Invalid choice. Please try again.")
            continue

        # List all available images and let user select by number
        images_dir = "images"
        image_files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f)) and 
                      f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

        if not image_files:
            print(f"Error: No image files found in {images_dir} directory.")
            continue

        print("\nAvailable images:")
        for i, img in enumerate(image_files, 1):
            print(f"{i}. {img}")

        selection = input("\nEnter the number of the image to process: ")
        try:
            selection_idx = int(selection) - 1
            if selection_idx < 0 or selection_idx >= len(image_files):
                print("Invalid selection. Please try again.")
                continue
            selected_image = image_files[selection_idx]
            input_path = os.path.join(images_dir, selected_image)
        except ValueError:
            print("Please enter a valid number.")
            continue

        # Always use the output directory
        os.makedirs("output", exist_ok=True)
        output_path = None  # Will be set to use the output directory in ensure_output_path

        # Ask if the user wants to display results
        display_result = input("\nDo you want to display the processed image? (y/n): ").lower() == 'y'

        # Select a processing type
        print("\nSelect processing type:")
        print("1. Edge Detection")
        print("2. Image Sharpening")
        print("3. Apply Filters")
        print("4. Back to main menu")

        choice = input("\nEnter your choice (1-4): ")

        if choice == '4':
            # Go back to main menu
            continue
        elif choice == '1':
            # Edge detection options
            print("\nEdge Detection Options:")
            method = "canny"  # Currently only canny is supported

            blur = input("Enter Gaussian blur sigma value (default: 1.0): ")
            blur = float(blur) if blur else 1.0

            high_threshold = input("Enter high threshold for edge detection (default: 91): ")
            high_threshold = int(high_threshold) if high_threshold else 91

            low_threshold = input("Enter low threshold for edge detection (default: 31): ")
            low_threshold = int(low_threshold) if low_threshold else 31

            # Process
            output = ensure_output_path(output_path, input_path, "edge")
            detect_edges(
                input_path,
                output_path=output,
                method=method,
                blur=blur,
                high_threshold=high_threshold,
                low_threshold=low_threshold,
                display_result=display_result
            )
            print(f"Edge detection completed. Output saved to {output}")

        elif choice == '2':
            # Image sharpening options
            print("\nImage Sharpening Options:")
            print("Available methods:")
            print("1. Unsharp Mask")
            print("2. OpenCV (cv2)")
            print("3. TensorFlow")

            method_choice = input("Select method (1-3, default: 1): ")
            if method_choice == '2':
                method = "cv2"
            elif method_choice == '3':
                method = "tensorflow"
            else:
                method = "unsharp_mask"

            blur_kernel_size = input("Enter blur kernel size (default: 7): ")
            blur_kernel_size = int(blur_kernel_size) if blur_kernel_size else 7

            sharpening_amount = input("Enter sharpening amount (default: 1.5): ")
            sharpening_amount = float(sharpening_amount) if sharpening_amount else 1.5

            threshold = input("Enter threshold (default: 10): ")
            threshold = int(threshold) if threshold else 10

            # Process
            output = ensure_output_path(output_path, input_path, "sharp")
            sharpen_image(
                input_path,
                output_path=output,
                method=method,
                blur_kernel_size=blur_kernel_size,
                sharpening_amount=sharpening_amount,
                threshold=threshold,
                display_result=display_result
            )
            print(f"Image sharpening completed. Output saved to {output}")

        elif choice == '3':
            # Filter options
            print("\nFilter Options:")
            print("1. Apply a specific filter")
            print("2. Apply all filters")
            print("3. Back to processing type selection")

            filter_choice = input("Select option (1-3): ")

            if filter_choice == '3':
                # Go back to processing type selection
                continue
            elif filter_choice == '1':
                print("\nAvailable filters: BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EDGE_ENHANCE_MORE, EMBOSS, FIND_EDGES, SHARPEN, SMOOTH, SMOOTH_MORE")
                filter_name = input("Enter filter name: ").lower()

                # Process
                output = ensure_output_path(output_path, input_path, filter_name)
                apply_single_filter(
                    input_path,
                    filter_name=filter_name,
                    output_path=output,
                    display_result=display_result
                )
                print(f"Filter '{filter_name}' applied. Output saved to {output}")
            elif filter_choice == '2':
                # Apply all filters
                apply_pil_filters(
                    input_path,
                    display_result=display_result
                )
                print("All filters applied and displayed.")
            else:
                print("Invalid choice. Returning to main menu.")
        else:
            print("Invalid choice. Returning to main menu.")

if __name__ == "__main__":
    # If no arguments are provided, run the interactive menu
    import sys
    if len(sys.argv) == 1:
        interactive_menu()
    else:
        main()
