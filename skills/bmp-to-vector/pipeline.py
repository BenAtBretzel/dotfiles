import subprocess
import json
import base64
import urllib.request
import logging
import os
from typing import Dict, Any
from merge import merge_semantics

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

OLLAMA_URL = "http://localhost:11434/api/generate"

def run_potrace(input_bmp: str, output_svg: str) -> None:
    """Generates raw SVG paths from bitmap."""
    cmd = ["potrace", input_bmp, "-s", "-o", output_svg]
    subprocess.run(cmd, check=True)
    logging.info(f"Potrace generated raw SVG: {output_svg}")

def get_vlm_semantics(image_path: str, model: str) -> Dict[str, Any]:
    """Retrieves semantic bounding boxes and OCR from local VLM or returns mock data."""
    if model == "mock":
        logging.warning("VLM model set to 'mock'. Returning mock semantic data for testing.")
        return {
            "objects": [
                {
                    "type": "container",
                    "box": [20, 20, 180, 180],
                    "content": "main square"
                },
                {
                    "type": "text",
                    "box": [50, 80, 150, 120],
                    "content": "HELLO"
                }
            ]
        }

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = """
    Analyze this image and output ONLY valid JSON.
    Format: {"objects": [{"type": "text|icon|container", "box": [x1, y1, x2, y2], "content": "..."}]}
    Note: [x1, y1, x2, y2] are absolute pixel coordinates corresponding to the input image dimensions (0 to image_width, 0 to image_height).
    """
    
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "format": "json",
        "stream": False
    }
    
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        logging.info("VLM generated semantic map.")
        return json.loads(result["response"])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hybrid semantic bitmap-to-vector pipeline.")
    parser.add_argument("model", help="Ollama VLM model name to use (use 'mock' for offline testing)")
    parser.add_argument("input_path", help="Path to input bitmap (.bmp) file")
    parser.add_argument("output_path", help="Path to output SVG (.svg) file")
    
    args = parser.parse_args()
    
    raw_svg = args.input_path.replace(".bmp", "_raw.svg")
    
    run_potrace(args.input_path, raw_svg)
    semantic_data = get_vlm_semantics(args.input_path, args.model)
    merge_semantics(raw_svg, semantic_data, args.output_path)
