import xml.etree.ElementTree as ET
import logging
import re
import os
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
    """Merges VLM semantic annotations with Potrace raw vector paths."""
    if not os.path.exists(raw_svg_path):
        raise FileNotFoundError(f"Raw SVG path not found: {raw_svg_path}")
        
    tree = ET.parse(raw_svg_path)
    root = tree.getroot()
    
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    main_g = root.find('.//svg:g', ns)
    if main_g is None:
        logging.warning("No transformed group found in raw SVG. Using root.")
        main_g = root
        
    transform_str = main_g.get('transform', '')
    tx, ty, sx, sy = parse_transform(transform_str)
    
    paths = main_g.findall('.//svg:path', ns)
    objects = semantics.get('objects', [])
    
    logging.info(f"Merging semantic annotations: parsed {len(paths)} raw SVG paths, matching against {len(objects)} semantic VLM objects...")
    
    obj_paths = {i: [] for i in range(len(objects))}
    text_paths = set()
    
    for path in paths:
        d_attr = path.get('d', '')
        points = parse_svg_path(d_attr)
        if not points:
            continue
            
        pixel_x = [pt[0] * sx + tx for pt in points]
        pixel_y = [pt[1] * sy + ty for pt in points]
        
        min_x, max_x = min(pixel_x), max(pixel_x)
        min_y, max_y = min(pixel_y), max(pixel_y)
        
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        
        matched_idx = None
        for i, obj in enumerate(objects):
            box = obj.get('box', [])
            if len(box) == 4:
                ox1, oy1, ox2, oy2 = box
                if ox1 <= cx <= ox2 and oy1 <= cy <= oy2:
                    matched_idx = i
                    break
                    
        if matched_idx is not None:
            obj = objects[matched_idx]
            if obj.get('type') == 'text':
                text_paths.add(path)
            else:
                obj_paths[matched_idx].append(path)
                
    for path in text_paths:
        if path in main_g:
            main_g.remove(path)
            
    for i, obj in enumerate(objects):
        obj_type = obj.get('type')
        if obj_type == 'text':
            box = obj.get('box', [])
            if len(box) == 4:
                ox1, oy1, ox2, oy2 = box
                content = obj.get('content', '')
                
                font_size = max(10.0, oy2 - oy1)
                text_elem = ET.Element('{http://www.w3.org/2000/svg}text', {
                    'x': str(ox1),
                    'y': str(oy2 - font_size * 0.1),
                    'font-size': f"{font_size}px",
                    'font-family': 'sans-serif',
                    'fill': '#000000'
                })
                text_elem.text = content
                root.append(text_elem)
        else:
            matching_paths = obj_paths[i]
            if matching_paths:
                group_id = f"vlm-{obj_type}-{i}"
                g_elem = ET.Element('{http://www.w3.org/2000/svg}g', {
                    'id': group_id,
                    'class': obj_type,
                    'metadata': obj.get('content', '')
                })
                
                for path in matching_paths:
                    if path in main_g:
                        main_g.remove(path)
                    g_elem.append(path)
                    
                main_g.append(g_elem)
                
    grouped_count = sum(len(matching_paths) for matching_paths in obj_paths.values())
    replaced_count = len(text_paths)
    text_count = len([o for o in objects if o.get('type') == 'text'])
    logging.info(f"Grouping complete: grouped {grouped_count} paths into semantic containers/icons. Replaced {replaced_count} traced paths with {text_count} clean text node(s).")

    tree.write(output_path)
    logging.info(f"Merged SVG saved to: {output_path}")
