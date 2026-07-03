import xml.etree.ElementTree as ET
import logging
import re
from typing import Dict, Any, List, Tuple

# Register SVG namespace to prevent 'ns0:' prefixing in written SVG output
ET.register_namespace('', 'http://www.w3.org/2000/svg')

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

    # Create a new root element for the merged SVG
    merged_root = ET.Element("svg", {"width": "100%", "height": "100%"})
    root.replace_child(merged_root, None)

    # Add semantic objects as <g> elements
    for obj in semantics["objects"]:
        group = ET.SubElement(merged_root, "g", {"class": obj["type"]})  # Use type for grouping
        box = ET.SubElement(group, "rect", {
            "x": str(obj["box"][0]),
            "y": str(obj["box"][1]),
            "width": str(obj["box"][2] - obj["box"][0]),
            "height": str(obj["box"][3] - obj["box"][1])
        })
        content_text = ET.SubElement(group, "text", {
            "x": str(obj["box"][0] + 5),  # Adjust position as needed
            "y": str(obj["box"][1] + 10), # Adjust position as needed
            "font-family": "Arial",
            "font-size": "12px",
            "fill": "black"
        })
        content_text.text = obj["content"]

    tree = ET.ElementTree(merged_root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    logging.info(f"Merged SVG saved to: {output_path}")


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
