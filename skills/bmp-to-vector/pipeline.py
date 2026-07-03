import subprocess
import json
import base64
import urllib.request
import xml.etree.ElementTree as ET
import logging
import os
import re
from typing import Dict, Any, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Register SVG namespace to prevent 'ns0:' prefixing in written SVG output
ET.register_namespace('', 'http://www.w3.org/2000/svg')

OLLAMA_URL = "http://localhost:11434/api/generate"
VLM_MODEL = os.environ.get("VLM_MODEL")

def parse_svg_path(d_string: str) -> List[Tuple[float, float]]:
    """Parses SVG path coordinates from a 'd' attribute string.
    
    Supports move (M/m), line (L/l), cubic bezier (C/c), and close (Z/z) commands.
    """
    if not d_string:
        return []
        
    tokens = re.findall(r'[a-zA-Z]|[-+]?\d+(?:\.\d+)?', d_string)
    if not tokens:
        return []
        
    points: List[Tuple[float, float]] = []
    curr_x, curr_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    cmd = ''
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            cmd = token
            i += 1
            
        cmd_lower = cmd.lower()
        if cmd_lower in ('m', 'l'):
            if i + 2 > len(tokens):
                break
            try:
                x = float(tokens[i])
                y = float(tokens[i+1])
            except ValueError as e:
                raise ValueError(f"Invalid numeric value in path coordinates: {tokens[i]}, {tokens[i+1]}") from e
            i += 2
            if cmd.isupper():
                curr_x, curr_y = x, y
            else:
                curr_x += x
                curr_y += y
            points.append((curr_x, curr_y))
            if cmd_lower == 'm':
                start_x, start_y = curr_x, curr_y
                cmd = 'l' if cmd == 'm' else 'L'
        elif cmd_lower == 'c':
            if i + 6 > len(tokens):
                break
            try:
                x1, y1 = float(tokens[i]), float(tokens[i+1])
                x2, y2 = float(tokens[i+2]), float(tokens[i+3])
                x3, y3 = float(tokens[i+4]), float(tokens[i+5])
            except ValueError as e:
                raise ValueError(f"Invalid numeric value in path cubic coordinates: {tokens[i:i+6]}") from e
            i += 6
            if cmd.isupper():
                curr_x, curr_y = x3, y3
                points.append((x1, y1))
                points.append((x2, y2))
                points.append((x3, y3))
            else:
                points.append((curr_x + x1, curr_y + y1))
                points.append((curr_x + x2, curr_y + y2))
                curr_x += x3
                curr_y += y3
                points.append((curr_x, curr_y))
        elif cmd_lower == 'z':
            curr_x, curr_y = start_x, start_y
            points.append((curr_x, curr_y))
        else:
            i += 1
            
    return points

def parse_transform(transform_str: str) -> Tuple[float, float, float, float]:
    """Parses SVG transform translate and scale parameters.
    
    Returns (tx, ty, sx, sy). Defaults to (0.0, 0.0, 1.0, 1.0).
    """
    tx, ty = 0.0, 0.0
    sx, sy = 1.0, 1.0
    
    if not transform_str:
        return tx, ty, sx, sy
        
    translate_match = re.search(r'translate\(([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\)', transform_str)
    if translate_match:
        try:
            tx = float(translate_match.group(1))
            ty = float(translate_match.group(2))
        except ValueError as e:
            raise ValueError(f"Invalid translate values in transform: {transform_str}") from e
            
    scale_match = re.search(r'scale\(([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\)', transform_str)
    if scale_match:
        try:
            sx = float(scale_match.group(1))
            sy = float(scale_match.group(2))
        except ValueError as e:
            raise ValueError(f"Invalid scale values in transform: {transform_str}") from e
            
    return tx, ty, sx, sy

def run_potrace(input_bmp: str, output_svg: str) -> None:
    """Generates raw SVG paths from bitmap."""
    cmd = ["potrace", input_bmp, "-s", "-o", output_svg]
    subprocess.run(cmd, check=True)
    logging.info(f"Potrace generated raw SVG: {output_svg}")

def get_vlm_semantics(image_path: str) -> Dict[str, Any]:
    """Retrieves semantic bounding boxes and OCR from local VLM or returns mock data."""
    if not VLM_MODEL:
        logging.warning("VLM_MODEL environment variable not set. Returning mock semantic data for testing.")
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
