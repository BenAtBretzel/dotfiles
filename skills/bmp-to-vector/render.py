"""SVG-to-raster rendering and image cropping utilities."""

import logging
import os
import subprocess
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def render_svg(svg_path: str, output_path: str, density: int = 150) -> str:
    """Render an SVG file to a raster image using ImageMagick.

    Executes ``magick <svg_path> -density <density> <output_path>``.

    Args:
        svg_path: Path to the source SVG file.
        output_path: Desired path for the rendered raster image.
        density: Pixel density (DPI) for rasterisation.

    Returns:
        *output_path* on success.

    Raises:
        FileNotFoundError: If *svg_path* does not exist.
        RuntimeError: If the ``magick`` command exits with a non-zero code.
    """
    if not os.path.isfile(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    cmd = ["magick", svg_path, "-density", str(density), output_path]
    logger.info("Running: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"magick failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    logger.info("Rendered %s -> %s at %d DPI", svg_path, output_path, density)
    return output_path


def crop_region(
    img: np.ndarray, row: int, col: int, grid: int
) -> Tuple[np.ndarray, int, int, int, int]:
    """Crop a single grid cell from an image.

    The image is conceptually divided into a *grid* x *grid* matrix of
    tiles.  This function returns a copy of the tile at (*row*, *col*).

    Args:
        img: Source image (any channel count).
        row: Zero-based tile row index.
        col: Zero-based tile column index.
        grid: Number of tiles along each axis.

    Returns:
        Tuple of (cropped_image_copy, x_offset, y_offset,
        tile_width, tile_height).

    Raises:
        ValueError: If *img* is None, *grid* < 1, or *row*/*col* are
            out of range.
    """
    if img is None:
        raise ValueError("img must not be None.")
    if grid < 1:
        raise ValueError(f"grid must be >= 1, got {grid}")
    if not (0 <= row < grid):
        raise ValueError(f"row {row} out of range for grid size {grid}")
    if not (0 <= col < grid):
        raise ValueError(f"col {col} out of range for grid size {grid}")

    h, w = img.shape[:2]
    tile_h = h // grid
    tile_w = w // grid

    y0 = row * tile_h
    x0 = col * tile_w
    # Last tile absorbs remainder pixels.
    y1 = h if row == grid - 1 else y0 + tile_h
    x1 = w if col == grid - 1 else x0 + tile_w

    cropped = img[y0:y1, x0:x1].copy()
    return cropped, x0, y0, x1 - x0, y1 - y0


def load_image(path: str) -> np.ndarray:
    """Load an image from disk via OpenCV.

    Args:
        path: Filesystem path to the image.

    Returns:
        BGR numpy array.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file exists but could not be decoded as an image.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Failed to decode image: {path}")

    logger.info("Loaded image %s (%dx%d)", path, img.shape[1], img.shape[0])
    return img


def save_image(img: np.ndarray, path: str) -> str:
    """Save an image to disk via OpenCV.

    Args:
        img: Image array to write.
        path: Destination file path.

    Returns:
        *path* on success.

    Raises:
        ValueError: If *img* is None.
    """
    if img is None:
        raise ValueError("img must not be None.")

    cv2.imwrite(path, img)
    logger.info("Saved image to %s", path)
    return path
