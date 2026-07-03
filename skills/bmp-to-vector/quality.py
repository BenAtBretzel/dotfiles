"""SSIM computation, region-level scoring, accept/reject gate, and checkpoint management."""

import logging
import os
import shutil
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

GATE_EPSILON: float = 0.001


def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Compute SSIM between two images.

    Images may be BGR or single-channel grayscale.  BGR inputs are
    converted to grayscale internally before the comparison.

    Args:
        img1: First image (BGR or grayscale).
        img2: Second image (BGR or grayscale).

    Returns:
        SSIM value in [0, 1].

    Raises:
        ValueError: If either image is None or dimensions do not match.
    """
    if img1 is None or img2 is None:
        raise ValueError("Both images must be non-None.")
    if img1.shape[:2] != img2.shape[:2]:
        raise ValueError(
            f"Image dimensions must match: {img1.shape[:2]} vs {img2.shape[:2]}"
        )

    # Convert to grayscale if needed.
    if img1.ndim == 3 and img1.shape[2] >= 3:
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    else:
        g1 = img1 if img1.ndim == 2 else img1[:, :, 0]

    if img2.ndim == 3 and img2.shape[2] >= 3:
        g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        g2 = img2 if img2.ndim == 2 else img2[:, :, 0]

    g1 = g1.astype(np.float64)
    g2 = g2.astype(np.float64)

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    mu1 = cv2.GaussianBlur(g1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(g2, (11, 11), 1.5)

    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(g1 * g1, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(g2 * g2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(g1 * g2, (11, 11), 1.5) - mu1_mu2

    numerator = (2 * mu1_mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)

    ssim_map = numerator / denominator
    return float(np.mean(ssim_map))


def ssim_grid(source: np.ndarray, render: np.ndarray, grid: int = 4) -> np.ndarray:
    """Compute per-tile SSIM over a grid decomposition of the images.

    Args:
        source: Source image (BGR or grayscale).
        render: Rendered image (BGR or grayscale).
        grid: Number of tiles along each axis.

    Returns:
        A (grid, grid) numpy array of SSIM values.

    Raises:
        ValueError: If grid < 1 or any tile dimension is smaller than the
            11-pixel SSIM kernel minimum.
    """
    if grid < 1:
        raise ValueError(f"grid must be >= 1, got {grid}")

    h, w = source.shape[:2]
    tile_h = h // grid
    tile_w = w // grid

    if tile_h < 11 or tile_w < 11:
        raise ValueError(
            f"Tile dimensions ({tile_w}x{tile_h}) are below the 11px "
            f"SSIM kernel minimum. Use a smaller grid or larger images."
        )

    scores = np.zeros((grid, grid), dtype=np.float64)
    for r in range(grid):
        for c in range(grid):
            y0 = r * tile_h
            x0 = c * tile_w
            # Last tile absorbs any remainder pixels.
            y1 = h if r == grid - 1 else y0 + tile_h
            x1 = w if c == grid - 1 else x0 + tile_w
            scores[r, c] = compute_ssim(source[y0:y1, x0:x1], render[y0:y1, x0:x1])

    return scores


def worst_region(scores: np.ndarray) -> Tuple[int, int, float]:
    """Find the grid cell with the lowest SSIM score.

    Args:
        scores: A 2-D array of SSIM values (e.g. from ``ssim_grid``).

    Returns:
        Tuple of (row, col, score) for the worst cell.

    Raises:
        ValueError: If the array is empty.
    """
    if scores.size == 0:
        raise ValueError("scores array must not be empty.")

    idx = int(np.argmin(scores))
    row, col = np.unravel_index(idx, scores.shape)
    return int(row), int(col), float(scores[row, col])


def accept_change(
    current_global: float,
    new_global: float,
    current_region: float,
    new_region: float,
) -> bool:
    """Decide whether to accept a proposed SVG change.

    Accepts only when BOTH global and region SSIM have improved by more
    than ``GATE_EPSILON``.

    Args:
        current_global: Current global SSIM.
        new_global: Proposed global SSIM.
        current_region: Current worst-region SSIM.
        new_region: Proposed worst-region SSIM.

    Returns:
        True if the change should be accepted.
    """
    global_improved = (new_global - current_global) > GATE_EPSILON
    region_improved = (new_region - current_region) > GATE_EPSILON
    return global_improved and region_improved


def is_marginal(current_global: float, new_global: float) -> bool:
    """Check whether the global SSIM delta falls in the marginal zone.

    A marginal delta is one in [-GATE_EPSILON, 3*GATE_EPSILON], indicating
    that a VLM tiebreaker may be needed.

    Args:
        current_global: Current global SSIM.
        new_global: Proposed global SSIM.

    Returns:
        True if the delta is marginal.
    """
    delta = new_global - current_global
    return -GATE_EPSILON <= delta <= 3 * GATE_EPSILON


class CheckpointManager:
    """Manages numbered SVG checkpoints for safe rollback.

    Each call to ``save`` copies the current SVG into the checkpoint
    directory with an incrementing 4-digit sequence number.  ``restore``
    copies the most recent checkpoint back to the working SVG path.
    """

    def __init__(self, checkpoint_dir: str) -> None:
        """Initialise the checkpoint manager.

        Args:
            checkpoint_dir: Directory in which to store checkpoint copies.
                Created automatically if it does not exist.
        """
        self._dir = checkpoint_dir
        self._counter = 0
        os.makedirs(self._dir, exist_ok=True)
        logger.info("CheckpointManager initialised at %s", self._dir)

    @property
    def count(self) -> int:
        """Number of checkpoints saved so far."""
        return self._counter

    def save(self, svg_path: str) -> str:
        """Save a checkpoint copy of the given SVG file.

        Args:
            svg_path: Path to the SVG file to checkpoint.

        Returns:
            Absolute path of the newly created checkpoint file.

        Raises:
            FileNotFoundError: If *svg_path* does not exist.
        """
        if not os.path.isfile(svg_path):
            raise FileNotFoundError(f"SVG file not found: {svg_path}")

        dest = os.path.join(self._dir, f"checkpoint_{self._counter:04d}.svg")
        shutil.copy2(svg_path, dest)
        self._counter += 1
        logger.info("Saved checkpoint %s", dest)
        return dest

    def restore(self, svg_path: str) -> str:
        """Restore the latest checkpoint back to *svg_path*.

        Args:
            svg_path: Destination path to overwrite with the checkpoint.

        Returns:
            Path of the checkpoint file that was used.

        Raises:
            RuntimeError: If no checkpoints have been saved yet.
        """
        if self._counter == 0:
            raise RuntimeError("No checkpoints available to restore.")

        latest = os.path.join(
            self._dir, f"checkpoint_{self._counter - 1:04d}.svg"
        )
        if not os.path.isfile(latest):
            raise FileNotFoundError(
                f"Expected checkpoint file missing: {latest}"
            )

        shutil.copy2(latest, svg_path)
        logger.info("Restored %s from %s", svg_path, latest)
        return latest
