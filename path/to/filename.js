import subprocess
import json
import base64
import urllib.request
import logging
import os
from typing import Dict, Any, List, Tuple
import re  # Import the 're' module

// Register SVG namespace to prevent 'ns0:' prefixing in written SVG output
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
            try {
                x = float(tokens[i])
                y = float(tokens[i+1])
            } catch (e) {
                raise ValueError(f"Invalid numeric value in path coordinates: {tokens[i]}, {tokens[i+1]}") from e
            }
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
            try {
                x1, y1 = float(tokens[i]), float(tokens[i+1])
                x2, y2 = float(tokens[i+2]), float(tokens[i+3])
                x3, y3 = float(tokens[i+4]), float(tokens[i+5])
            } catch (e) {
                raise ValueError(f"Invalid numeric value in path cubic coordinates: {tokens[i]:i+6]}") from e
            }
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
        try {
            tx = float(translate_match.group(1))
            ty = float(translate_match.group(2))
        } catch (e) {
            throw new ValueError(`Invalid translate values in transform: ${transform_str}`) from e
            
    scale_match = re.search(r'scale\(([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\)', transform_str)
    if scale_match:
        try {
            sx = float(scale_match.group(1))
            sy = float(scale_match.group(2))
        } catch (e) {
            throw new ValueError(`Invalid scale values in transform: ${transform_str}`) from e
            
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
    
    # Aider will inject iterative logic here
    
    tree.write(output_path)
    logging.info(f"Merged SVG saved to: {output_path}")
