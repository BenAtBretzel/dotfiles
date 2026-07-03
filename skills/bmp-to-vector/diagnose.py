"""VLM-based comparison of source image vs SVG render to diagnose quality problems.

Uses a local Ollama instance to send image pairs to a vision-language model,
which identifies specific discrepancies between the original photograph and
its vector illustration rendering.
"""

import base64
import json
import logging
import os
import re
import urllib.request

logger = logging.getLogger(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'


def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from model output.

    Args:
        text: Raw model response text.

    Returns:
        Text with all think-tag blocks removed and leading/trailing
        whitespace stripped.
    """
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def _encode_image(path: str) -> str:
    """Read an image file and return its base64-encoded string.

    Args:
        path: Absolute or relative path to the image file.

    Returns:
        Base64-encoded string of the file contents.

    Raises:
        FileNotFoundError: If the image file does not exist.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image file not found: {path}")
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _ollama_generate(model: str, prompt: str, images: list) -> str:
    """Send a multimodal generate request to the Ollama API.

    Args:
        model: Name of the Ollama model to use.
        prompt: Text prompt to send alongside the images.
        images: List of base64-encoded image strings.

    Returns:
        The response text from the model.

    Raises:
        RuntimeError: If the Ollama API request fails or returns an
            unexpected response.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images,
        "stream": False,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise RuntimeError(f"Ollama API request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Ollama API returned invalid JSON: {exc}"
        ) from exc

    if "response" not in body:
        raise RuntimeError(
            f"Ollama API response missing 'response' key: {body}"
        )
    return body["response"]


def diagnose_region(
    source_crop_path: str,
    render_crop_path: str,
    model: str = 'gemma3:4b',
) -> str:
    """Compare a source photograph crop against its vector render crop.

    Sends both images to a vision-language model which identifies specific
    quality problems in the vector illustration relative to the original.

    Args:
        source_crop_path: Path to the cropped source photograph.
        render_crop_path: Path to the cropped vector render.
        model: Ollama model name to use for diagnosis.

    Returns:
        A plain-text diagnosis string describing discrepancies.

    Raises:
        FileNotFoundError: If either image path does not exist.
        RuntimeError: If the Ollama API call fails.
    """
    if not os.path.isfile(source_crop_path):
        raise FileNotFoundError(
            f"Source crop image not found: {source_crop_path}"
        )
    if not os.path.isfile(render_crop_path):
        raise FileNotFoundError(
            f"Render crop image not found: {render_crop_path}"
        )

    img1_b64 = _encode_image(source_crop_path)
    img2_b64 = _encode_image(render_crop_path)

    prompt = (
        "Image 1 is a photograph. Image 2 is a vector illustration of the "
        "same region.\nDescribe specifically what the illustration gets "
        "wrong: missing shapes, wrong colors,\nlost detail, merged regions "
        "that should be separate. Be concise."
    )

    logger.info(
        "Diagnosing region: source=%s render=%s model=%s",
        source_crop_path, render_crop_path, model,
    )
    logger.info("Querying Ollama VLM for regional diagnosis...")
    raw = _ollama_generate(model, prompt, [img1_b64, img2_b64])
    return _strip_think_tags(raw)


def tiebreak(
    source_path: str,
    before_path: str,
    after_path: str,
    model: str = 'gemma3:4b',
) -> str:
    """Ask a VLM which of two vector illustrations is more faithful.

    Args:
        source_path: Path to the original photograph.
        before_path: Path to the first vector illustration (candidate A).
        after_path: Path to the second vector illustration (candidate B).
        model: Ollama model name to use for comparison.

    Returns:
        'A' if the first illustration is more faithful or the response is
        ambiguous, 'B' if the second is clearly preferred.

    Raises:
        FileNotFoundError: If any image path does not exist.
        RuntimeError: If the Ollama API call fails.
    """
    if not os.path.isfile(source_path):
        raise FileNotFoundError(
            f"Source image not found: {source_path}"
        )
    if not os.path.isfile(before_path):
        raise FileNotFoundError(
            f"Before image not found: {before_path}"
        )
    if not os.path.isfile(after_path):
        raise FileNotFoundError(
            f"After image not found: {after_path}"
        )

    img_source = _encode_image(source_path)
    img_before = _encode_image(before_path)
    img_after = _encode_image(after_path)

    prompt = (
        "The original photograph is Image 1. Image 2 and Image 3 are two "
        "vector illustrations.\nWhich illustration is more faithful to the "
        "original? Reply with only 'A' for Image 2 or 'B' for Image 3."
    )

    logger.info(
        "Tiebreak: source=%s before=%s after=%s model=%s",
        source_path, before_path, after_path, model,
    )
    raw = _ollama_generate(
        model, prompt, [img_source, img_before, img_after]
    )
    cleaned = _strip_think_tags(raw).strip().upper()

    # Look for an unambiguous A or B answer.
    if 'B' in cleaned and 'A' not in cleaned:
        return 'B'
    if 'A' in cleaned and 'B' not in cleaned:
        return 'A'

    # Ambiguous or unclear -- conservative default keeps current.
    logger.warning(
        "Tiebreak response ambiguous ('%s'), defaulting to 'A'", cleaned
    )
    return 'A'
