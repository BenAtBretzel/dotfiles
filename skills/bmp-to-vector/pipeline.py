import subprocess
import json
import base64
import urllib.request
import xml.etree.ElementTree as ET
import logging
import os
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

OLLAMA_URL = "http://localhost:11434/api/generate"

VLM_MODEL = os.environ.get("VLM_MODEL")
if not VLM_MODEL:
    raise ValueError("Environment variable VLM_MODEL is required but not set")

def run_potrace(input_bmp: str, output_svg: str) -> None:
    """Generates raw SVG paths from bitmap."""
    cmd = ["potrace", input_bmp, "-s", "-o", output_svg]
    subprocess.run(cmd, check=True)
    logging.info(f"Potrace generated raw SVG: {output_svg}")

def get_vlm_semantics(image_path: str) -> Dict[str, Any]:
    """Retrieves semantic bounding boxes and OCR from local VLM."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = """
    Analyze this image and output ONLY valid JSON.
    Format: {"objects": [{"type": "text|icon|container", "box": [x1, y1, x2, y2], "content": "..."}]}
    """
    
    payload = {
        "model": VLM_MODEL,
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

def merge_semantics(raw_svg_path: str, semantics: Dict[str, Any], output_path: str) -> None:
    """
    TODO for Aider: Implement coordinate intersection and SVG DOM manipulation here.
    1. Parse raw_svg_path using ET.parse.
    2. Iterate through semantics['objects'].
    3. Group Potrace paths that fall within the VLM bounding boxes into semantic <g> tags.
    4. Replace raw traced text paths with actual SVG <text> nodes based on OCR content.
    5. Save to output_path.
    """
    tree = ET.parse(raw_svg_path)
    root = tree.getroot()
    
    # Aider will inject iterative logic here
    
    tree.write(output_path)
    logging.info(f"Merged SVG saved to: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python pipeline.py <input.bmp> <final.svg>")
        sys.exit(1)
        
    in_file, out_file = sys.argv[1], sys.argv[2]
    raw_svg = in_file.replace(".bmp", "_raw.svg")
    
    run_potrace(in_file, raw_svg)
    semantic_data = get_vlm_semantics(in_file)
    merge_semantics(raw_svg, semantic_data, out_file)
