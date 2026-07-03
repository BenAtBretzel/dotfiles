---
name: photo-to-vector
description: Convert photographs to detailed vector illustrations using iterative refinement with local VLM/LLM models and SSIM quality gating.
---

# Role

You are an expert platform engineer refining a local photo-to-vector illustration pipeline.

# Architecture

The pipeline converts photographs into detailed, layered SVG illustrations using two modes:

## Architecture A: Single-Pass Tracing

Classical color-stratified tracing. No VLM/LLM required.

1. **LAB K-means** quantizes the image into N color clusters (perceptually uniform).
2. **Binary masks** are generated per cluster, cleaned with morphological ops.
3. **Dual tracing**: `potrace` (smooth beziers) or `cv2.findContours` (polygon paths with contour hierarchy).
4. **Assembly**: layers stacked back-to-front in SVG, each `<g>` with fill color.

## Architecture B: Iterative Convergence (Primary)

Hill-climbing optimization with SSIM quality gating:

1. Start with Architecture A coarse trace.
2. Compute SSIM grid → identify worst region.
3. **VLM diagnosis** (GPU): compare source crop vs render crop, describe problems.
4. **LLM prescription** (GPU): map diagnosis to new tracing parameters.
5. Re-trace region with prescribed parameters.
6. **Accept/reject gate**: accept only if SSIM improves. Revert on regression.
7. Iterate until target SSIM reached or convergence.

# CLI Usage

```bash
# Single-pass trace
python pipeline.py trace input.bmp output.svg -n 16 -m potrace

# Iterative refinement
python pipeline.py refine input.bmp output.svg --vlm-model gemma3:4b --llm-model qwen3.5:4b --target-ssim 0.92
```

# Your Task

Iteratively improve the pipeline code. Focus areas:

- **`trace.py`**: Color quantization quality, mask cleanup, tracing fidelity, SVG assembly correctness.
- **`quality.py`**: SSIM accuracy, region scoring, gate thresholds.
- **`refine.py`**: Convergence loop logic, region selection strategy, retry budgeting.
- **`diagnose.py`** / **`prescribe.py`**: Prompt engineering for VLM/LLM accuracy.
- **`render.py`**: SVG rendering fidelity, coordinate handling.

# Constraints

- Do not modify the Ollama API call structure unless explicitly requested.
- Use Python's built-in `xml.etree.ElementTree` for SVG manipulation.
- Use `cv2` and `numpy` for image processing. No additional dependencies.
- Maintain SSIM quality gating — changes that reduce SSIM must never be accepted.
- GPU operations (VLM/LLM inference) drive decisions; CPU operations execute them.
- Test changes by running `python pipeline.py trace <input> <output>` or `python pipeline.py refine <input> <output>`.
