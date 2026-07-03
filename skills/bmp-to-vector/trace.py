"""Color-stratified multi-pass tracing engine.

LAB K-means quantization, binary mask generation, morphological cleanup,
dual tracing (potrace + cv2.findContours), multi-layer SVG assembly.
"""

import logging
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, fields
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

ET.register_namespace('', 'http://www.w3.org/2000/svg')
SVG_NS = 'http://www.w3.org/2000/svg'


@dataclass
class TraceParams:
    """Parameters controlling the tracing pipeline."""

    n_colors: int = 16
    turdsize: int = 2
    alphamax: float = 1.0
    opttolerance: float = 0.2
    method: str = "potrace"  # "potrace" or "contours"
    epsilon: float = 2.0     # cv2.approxPolyDP epsilon
    morph_kernel: int = 3    # kernel size, 0 to disable

    @classmethod
    def from_dict(cls, d: dict) -> "TraceParams":
        """Create a TraceParams from a dictionary, ignoring unknown keys.

        Args:
            d: Dictionary of parameter values. Keys not matching a known
               field are silently ignored.

        Returns:
            A new TraceParams instance populated from the dictionary.
        """
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


def quantize_colors(
    img: np.ndarray, n_colors: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Quantize an image to a fixed number of colors using LAB K-means.

    Args:
        img: BGR input image (H x W x 3, uint8).
        n_colors: Number of palette colors (must be >= 2).

    Returns:
        A tuple of (quantized_bgr, labels_2d, palette_bgr) where
        quantized_bgr has the same shape as img, labels_2d is (H x W)
        of int32 cluster indices, and palette_bgr is (n_colors x 1 x 3)
        in BGR uint8.

    Raises:
        ValueError: If img is None or n_colors < 2.
    """
    if img is None:
        raise ValueError("Input image must not be None.")
    if n_colors < 2:
        raise ValueError(
            f"n_colors must be >= 2, got {n_colors}."
        )

    h, w = img.shape[:2]

    # Convert to LAB for perceptually uniform clustering.
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    pixels = lab.reshape(-1, 3).astype(np.float32)

    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        20,
        1.0,
    )
    _, labels, centers = cv2.kmeans(
        pixels,
        n_colors,
        None,
        criteria,
        attempts=10,
        flags=cv2.KMEANS_PP_CENTERS,
    )

    # Reconstruct quantized LAB image and convert centers back to BGR.
    centers_uint8 = np.uint8(centers)
    quantized_lab = centers_uint8[labels.flatten()].reshape(h, w, 3)
    quantized_bgr = cv2.cvtColor(quantized_lab, cv2.COLOR_LAB2BGR)

    # Build palette in BGR by converting each center individually.
    palette_lab = centers_uint8.reshape(-1, 1, 3)
    palette_bgr = cv2.cvtColor(palette_lab, cv2.COLOR_LAB2BGR)

    labels_2d = labels.reshape(h, w)

    return quantized_bgr, labels_2d, palette_bgr


def generate_masks(labels: np.ndarray, n_colors: int) -> List[np.ndarray]:
    """Generate binary masks from cluster labels.

    Args:
        labels: 2-D array of cluster indices (H x W).
        n_colors: Number of distinct clusters.

    Returns:
        A list of uint8 masks, one per cluster, where foreground is 255.
    """
    masks: List[np.ndarray] = []
    for k in range(n_colors):
        mask = ((labels == k) * 255).astype(np.uint8)
        masks.append(mask)
    return masks


def cleanup_mask(mask: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply morphological close then open to remove noise from a mask.

    Args:
        mask: Single-channel uint8 binary mask.
        kernel_size: Size of the elliptical structuring element.
            If <= 0, the mask is returned unchanged.

    Returns:
        Cleaned mask (new array; input is not mutated).
    """
    if kernel_size <= 0:
        return mask

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
    )
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    return cleaned


def trace_potrace(
    mask: np.ndarray, params: TraceParams, work_dir: str
) -> Optional[ET.Element]:
    """Trace a binary mask to SVG paths using the potrace CLI.

    Args:
        mask: Single-channel uint8 mask (255 = foreground).
        params: Tracing parameters (turdsize, alphamax, opttolerance).
        work_dir: Directory for temporary BMP/SVG files.

    Returns:
        An SVG ``<g>`` element containing the traced paths, or None if
        potrace fails or produces no paths.
    """
    bmp_path = os.path.join(work_dir, "mask.bmp")
    svg_path = os.path.join(work_dir, "mask.svg")

    # Potrace treats black (0) as foreground, so invert our mask.
    inverted = cv2.bitwise_not(mask)
    cv2.imwrite(bmp_path, inverted)

    cmd = [
        "potrace",
        bmp_path,
        "-s",
        "-o", svg_path,
        "-t", str(params.turdsize),
        "-a", str(params.alphamax),
        "-O", str(params.opttolerance),
    ]

    try:
        subprocess.run(
            cmd, check=True, capture_output=True, text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        logger.warning("potrace failed: %s", exc)
        return None

    if not os.path.isfile(svg_path):
        logger.warning("potrace did not produce an SVG file.")
        return None

    try:
        tree = ET.parse(svg_path)
    except ET.ParseError as exc:
        logger.warning("Failed to parse potrace SVG: %s", exc)
        return None

    root = tree.getroot()

    # Potrace wraps paths in a <g> with a transform. Preserve it.
    g_elements = root.findall(f'.//{{{SVG_NS}}}g')
    paths = root.findall(f'.//{{{SVG_NS}}}path')

    if not paths:
        logger.debug("potrace produced no path elements.")
        return None

    # Determine the transform from the first <g> if present.
    transform = None
    if g_elements:
        transform = g_elements[0].get('transform')

    result_g = ET.Element(f'{{{SVG_NS}}}g')
    if transform:
        result_g.set('transform', transform)

    for path in paths:
        # Strip namespace-prefixed attributes for cleanliness; keep 'd'.
        new_path = ET.SubElement(result_g, f'{{{SVG_NS}}}path')
        d_attr = path.get('d')
        if d_attr:
            new_path.set('d', d_attr)
        # Carry over any style or other attributes.
        for attr_name, attr_val in path.attrib.items():
            if attr_name != 'd':
                new_path.set(attr_name, attr_val)

    return result_g


def contour_to_svg_path(contour: np.ndarray) -> str:
    """Convert an OpenCV contour to an SVG path ``d`` string.

    Args:
        contour: Contour array of shape (N, 1, 2) from cv2.findContours.

    Returns:
        SVG path data string (``M x0 y0 L x1 y1 ... Z``), or an empty
        string if the contour has fewer than 2 points.
    """
    pts = contour.reshape(-1, 2)
    if len(pts) < 2:
        return ""

    parts = [f"M {pts[0][0]} {pts[0][1]}"]
    for x, y in pts[1:]:
        parts.append(f"L {x} {y}")
    parts.append("Z")
    return " ".join(parts)


def trace_contours(
    mask: np.ndarray, params: TraceParams
) -> Optional[ET.Element]:
    """Trace a binary mask to SVG paths using cv2.findContours.

    Args:
        mask: Single-channel uint8 mask (255 = foreground).
        params: Tracing parameters (epsilon for polygon approximation).

    Returns:
        An SVG ``<g>`` element containing the traced paths, or None if
        no valid contours are found.
    """
    contours, _ = cv2.findContours(
        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    result_g = ET.Element(f'{{{SVG_NS}}}g')
    valid_count = 0

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, params.epsilon, True)
        if len(approx) < 3:
            continue

        d = contour_to_svg_path(approx)
        if not d:
            continue

        path_el = ET.SubElement(result_g, f'{{{SVG_NS}}}path')
        path_el.set('d', d)
        valid_count += 1

    if valid_count == 0:
        return None

    return result_g


def bgr_to_hex(bgr: np.ndarray) -> str:
    """Convert a BGR color array to a hex color string.

    Args:
        bgr: Array-like of (B, G, R) values (uint8).

    Returns:
        Hex color string in the form ``#rrggbb``.
    """
    b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
    return f"#{r:02x}{g:02x}{b:02x}"


def trace_image(
    img: np.ndarray,
    params: TraceParams,
    work_dir: Optional[str] = None,
) -> ET.Element:
    """Run the full color-stratified tracing pipeline on an image.

    Steps: quantize colors, generate per-color masks, morphological
    cleanup, trace each mask, and assemble into a multi-layer SVG.

    Args:
        img: BGR input image (H x W x 3, uint8).
        params: Tracing parameters.
        work_dir: Optional directory for intermediate files. A temporary
            directory is created (and cleaned up) if not provided.

    Returns:
        An SVG root ``ET.Element`` with one layer group per color.
    """
    tmp_dir_created = False
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="trace_")
        tmp_dir_created = True

    try:
        h, w = img.shape[:2]

        # Quantize.
        _, labels, palette = quantize_colors(img, params.n_colors)

        # Generate masks.
        masks = generate_masks(labels, params.n_colors)

        # Compute pixel area per color for sorting (largest first).
        areas = []
        for k in range(params.n_colors):
            area = int(np.count_nonzero(masks[k]))
            areas.append((area, k))
        areas.sort(key=lambda x: x[0], reverse=True)

        # Build SVG root.
        svg_root = ET.Element(f'{{{SVG_NS}}}svg')
        svg_root.set('width', str(w))
        svg_root.set('height', str(h))
        svg_root.set('viewBox', f'0 0 {w} {h}')

        traced_count = 0
        for area, k in areas:
            color_hex = bgr_to_hex(palette[k][0])

            cleaned = cleanup_mask(masks[k], params.morph_kernel)

            # Per-layer work directory for potrace files.
            layer_dir = os.path.join(work_dir, f"layer_{k}")
            os.makedirs(layer_dir, exist_ok=True)

            if params.method == "potrace":
                layer_g = trace_potrace(cleaned, params, layer_dir)
            elif params.method == "contours":
                layer_g = trace_contours(cleaned, params)
            else:
                logger.warning(
                    "Unknown tracing method '%s', falling back to "
                    "potrace.",
                    params.method,
                )
                layer_g = trace_potrace(cleaned, params, layer_dir)

            if layer_g is None:
                logger.debug(
                    "Layer %d (%s, area=%d) produced no paths, "
                    "skipping.",
                    k, color_hex, area,
                )
                continue

            layer_g.set('id', f'color-layer-{k}')
            layer_g.set('fill', color_hex)
            svg_root.append(layer_g)
            traced_count += 1

        logger.info(
            "Traced %d of %d color layers (%dx%d image).",
            traced_count, params.n_colors, w, h,
        )

        return svg_root

    finally:
        if tmp_dir_created and os.path.isdir(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)


def write_svg(svg_element: ET.Element, output_path: str) -> str:
    """Write an SVG element tree to a file.

    Args:
        svg_element: Root SVG ``ET.Element``.
        output_path: Destination file path.

    Returns:
        The output_path that was written to.
    """
    ET.indent(svg_element)
    tree = ET.ElementTree(svg_element)
    tree.write(output_path, xml_declaration=True, encoding='unicode')
    logger.info("Wrote SVG to %s", output_path)
    return output_path


def extract_n_colors_from_svg(svg_path: str) -> Optional[int]:
    """Extract the number of unique colors from an existing SVG file.

    Args:
        svg_path: Path to the SVG file.

    Returns:
        The number of unique colors found, or None if the file does not exist or
        cannot be parsed.
    """
    if not svg_path:
        return None
    if not os.path.isfile(svg_path):
        return None

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        colors = set()
        for elem in root.iter():
            fill = elem.get('fill')
            if fill and fill.startswith('#'):
                colors.add(fill.lower())
        if colors:
            return len(colors)
    except Exception as exc:
        logger.warning("Failed to parse SVG to extract colors: %s", exc)
    return None



def patch_region(
    svg_path: str,
    region_svg: ET.Element,
    row: int,
    col: int,
    grid: int,
    img_width: int,
    img_height: int,
    output_path: str,
) -> str:
    """Patch a region into an existing tiled SVG document.

    Removes any previous group for the given (row, col) position and
    inserts a new translated group containing the region's SVG children.

    Args:
        svg_path: Path to the existing SVG file.
        region_svg: SVG element whose children will be inserted.
        row: Row index in the tile grid.
        col: Column index in the tile grid.
        grid: Number of tiles per row/column.
        img_width: Full image width in pixels.
        img_height: Full image height in pixels.
        output_path: Destination file path for the patched SVG.

    Returns:
        The output_path that was written to.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    region_id = f"region-{row}-{col}"
    tw = img_width / grid
    th = img_height / grid

    # Remove any existing group for this region.
    for existing in root.findall(f'.//{{{SVG_NS}}}g[@id="{region_id}"]'):
        parent = root
        # Walk to find the direct parent of the element.
        for p in root.iter():
            if existing in list(p):
                parent = p
                break
        parent.remove(existing)

    # Build new region group with translation.
    region_g = ET.SubElement(root, f'{{{SVG_NS}}}g')
    region_g.set('id', region_id)
    region_g.set(
        'transform', f'translate({col * tw}, {row * th})'
    )

    for child in list(region_svg):
        region_g.append(child)

    ET.indent(root)
    tree.write(output_path, xml_declaration=True, encoding='unicode')
    logger.info(
        "Patched region (%d, %d) into %s", row, col, output_path
    )
    return output_path
