"""LLM-based parameter optimization for bitmap-to-vector tracing.

Given a VLM diagnosis of quality problems and the current tracing parameters,
this module queries a local Ollama LLM to suggest improved parameter values.
"""

import json
import logging
import re
import urllib.request

logger = logging.getLogger(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'

# Valid ranges for each parameter: (min, max, type)
_PARAM_RANGES = {
    "n_colors": (4, 64, int),
    "turdsize": (0, 10, int),
    "method": (None, None, str),
    "epsilon": (0.5, 5.0, float),
    "alphamax": (0.0, 1.34, float),
    "opttolerance": (0.0, 1.0, float),
    "morph_kernel": (0, 7, int),
}

_VALID_METHODS = {"potrace", "contours"}


def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from model output.

    Args:
        text: Raw model response text.

    Returns:
        Text with all think-tag blocks removed and leading/trailing
        whitespace stripped.
    """
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def _ollama_generate_text(model: str, prompt: str) -> str:
    """Send a text-only generate request to the Ollama API.

    Args:
        model: Name of the Ollama model to use.
        prompt: Text prompt to send.

    Returns:
        The response text from the model.

    Raises:
        RuntimeError: If the Ollama API request fails or returns an
            unexpected response.
    """
    payload = {
        "model": model,
        "prompt": prompt,
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


def _extract_json(text: str) -> dict:
    """Extract and parse a JSON object from noisy LLM output.

    Handles think tags, markdown code fences, trailing commas, and
    unbalanced braces.

    Args:
        text: Raw LLM response text that should contain a JSON object.

    Returns:
        Parsed dictionary from the extracted JSON.

    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    # Strip think tags first.
    cleaned = _strip_think_tags(text)

    # Strip markdown code fences (```json ... ``` or ``` ... ```).
    cleaned = re.sub(r'```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'```', '', cleaned)
    cleaned = cleaned.strip()

    # Find the outermost { ... } block.
    start = cleaned.find('{')
    if start == -1:
        raise ValueError(f"No JSON object found in response: {text[:200]}")

    # Walk forward to find matching closing brace.
    depth = 0
    end = -1
    for i in range(start, len(cleaned)):
        if cleaned[i] == '{':
            depth += 1
        elif cleaned[i] == '}':
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        # Unbalanced braces -- try appending a closing brace.
        json_str = cleaned[start:] + '}'
        logger.warning("Unbalanced braces in LLM JSON output, appending '}'")
    else:
        json_str = cleaned[start:end + 1]

    # Repair trailing commas before closing braces/brackets.
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse extracted JSON: {exc}. "
            f"Extracted text: {json_str[:300]}"
        ) from exc


def _clamp_params(params: dict) -> dict:
    """Enforce valid ranges on tracing parameters.

    Values outside their defined ranges are clamped to the nearest
    boundary. The 'method' field is validated against allowed values.
    Unknown keys are dropped.

    Args:
        params: Dictionary of parameter names to values.

    Returns:
        A new dictionary with all values clamped to valid ranges.
    """
    clamped = {}
    for key, (lo, hi, ptype) in _PARAM_RANGES.items():
        if key not in params:
            continue

        value = params[key]

        if key == "method":
            value = str(value).lower()
            if value not in _VALID_METHODS:
                logger.warning(
                    "Invalid method '%s', defaulting to 'potrace'", value
                )
                value = "potrace"
            clamped[key] = value
            continue

        try:
            value = ptype(value)
        except (TypeError, ValueError):
            logger.warning(
                "Cannot cast %s=%r to %s, skipping",
                key, value, ptype.__name__,
            )
            continue

        if lo is not None and value < lo:
            logger.info("Clamping %s from %s to minimum %s", key, value, lo)
            value = ptype(lo)
        if hi is not None and value > hi:
            logger.info("Clamping %s from %s to maximum %s", key, value, hi)
            value = ptype(hi)

        clamped[key] = value

    return clamped


def prescribe_params(
    diagnosis: str,
    current_params: dict,
    current_ssim: float,
    model: str = 'qwen3.5:4b',
) -> dict:
    """Use an LLM to suggest improved tracing parameters.

    Builds a prompt from the visual diagnosis and current parameters, sends
    it to a local Ollama instance, and parses the suggested parameter JSON.

    Args:
        diagnosis: Plain-text diagnosis from a VLM comparison.
        current_params: Current tracing parameter dictionary.
        current_ssim: Current regional SSIM score (0.0 to 1.0).
        model: Ollama model name to use for parameter suggestion.

    Returns:
        A dictionary of suggested parameters with values clamped to valid
        ranges. Returns current_params unchanged if the LLM response
        cannot be parsed.
    """
    if not diagnosis:
        logger.warning("Empty diagnosis provided, returning current params")
        return dict(current_params)

    prompt = (
        "You are optimizing parameters for a bitmap-to-vector tracing "
        "pipeline.\n\n"
        f"Current parameters: {json.dumps(current_params)}\n"
        f"Current regional SSIM score: {current_ssim:.4f} "
        "(1.0 = perfect match)\n\n"
        "Visual diagnosis of the current output:\n"
        f"{diagnosis}\n\n"
        "Suggest improved parameters as a JSON object with these keys:\n"
        '- "n_colors": int (number of color clusters, 4-64)\n'
        '- "turdsize": int (noise suppression, 0-10, lower = more detail)\n'
        '- "method": "potrace" or "contours"\n'
        '- "epsilon": float (path simplification, 0.5-5.0, '
        'lower = more detail)\n'
        '- "alphamax": float (corner threshold, 0.0-1.34)\n'
        '- "opttolerance": float (curve optimization, 0.0-1.0)\n'
        '- "morph_kernel": int (cleanup kernel size, 0-7, '
        '0 = no cleanup)\n\n'
        "Reply with ONLY valid JSON. No explanation."
    )

    logger.info(
        "Prescribing params: ssim=%.4f model=%s", current_ssim, model
    )
    logger.info("Querying Ollama LLM for parameter suggestions...")

    try:
        raw = _ollama_generate_text(model, prompt)
    except RuntimeError:
        logger.exception("Ollama API call failed, returning current params")
        return dict(current_params)

    try:
        parsed = _extract_json(raw)
    except ValueError:
        logger.warning(
            "Failed to extract JSON from LLM response, "
            "returning current params. Raw response: %s",
            raw[:300],
        )
        return dict(current_params)

    clamped = _clamp_params(parsed)

    if not clamped:
        logger.warning(
            "No valid parameters extracted after clamping, "
            "returning current params"
        )
        return dict(current_params)

    logger.info("Prescribed params: %s", clamped)
    return clamped
