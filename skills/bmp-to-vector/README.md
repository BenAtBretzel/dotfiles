# Photo-to-Vector Pipeline

A local, iterative pipeline for converting photographs to detailed vector illustrations using color-stratified tracing and VLM/LLM-guided refinement.

## Requirements

1. **System Dependencies**:
   - `potrace`
   - `imagemagick` (requires `magick` CLI)

2. **Python Dependencies**:
   - `numpy`
   - `opencv-python-headless` (cv2)

3. **Ollama Models** (Required for iterative refinement):
   - `gemma3:4b` (default vision model)
   - `qwen3.5:4b` (default parameter model)

## Usage

### 1. Single-Pass Tracing (Architecture A)

Traces an image using a classical color-stratified approach.

```bash
python pipeline.py trace input.png output.svg -n 16 -m potrace
```

Common options:
- `-n`, `--n-colors`: Number of color clusters (default: 16).
- `-m`, `--method`: Tracing method (`potrace` or `contours`).
- `-t`, `--turdsize`: Speckle noise suppression threshold (default: 2).
- `-k`, `--morph-kernel`: Morphological kernel size for mask cleanup (default: 3).

### 2. Iterative Refinement (Architecture B)

Uses local models to progressively improve vector detail based on regional SSIM quality scores.

```bash
python pipeline.py refine input.png output.svg --vlm-model gemma3:4b --llm-model qwen3.5:4b --target-ssim 0.92
```

Common options:
- `--vlm-model`: Ollama vision model for region diagnosis (default: `gemma3:4b`).
- `--llm-model`: Ollama text model for parameter prescription (default: `qwen3.5:4b`).
- `--grid`: Grid division size for SSIM scoring (default: 4, i.e., 16 regions).
- `--max-iterations`: Maximum refinement steps (default: 20).
- `--target-ssim`: Global SSIM target to stop optimization (default: 0.92).
