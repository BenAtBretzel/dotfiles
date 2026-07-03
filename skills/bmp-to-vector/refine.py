"""Iterative convergence loop for photo-to-vector refinement.

Implements the Architecture B hill-climbing optimization loop:
SSIM grid → worst region → VLM diagnose → LLM prescribe → re-trace → gate.
"""

import os
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional
from dataclasses import asdict

from quality import compute_ssim, ssim_grid, worst_region, accept_change, is_marginal
from quality import CheckpointManager, GATE_EPSILON
from render import render_svg, crop_region, load_image, save_image
from trace import trace_image, write_svg, patch_region, TraceParams
from diagnose import diagnose_region, tiebreak
from prescribe import prescribe_params

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


DEFAULT_INITIAL_PARAMS = TraceParams(
    n_colors=12,
    turdsize=5,
    alphamax=1.0,
    opttolerance=0.3,
    method="potrace",
    epsilon=2.0,
    morph_kernel=3,
)


def refine(
    source_path: str,
    output_path: str,
    vlm_model: str = "gemma3:4b",
    llm_model: str = "qwen3.5:4b",
    grid: int = 4,
    max_iterations: int = 20,
    max_retries_per_region: int = 3,
    target_ssim: float = 0.92,
    region_ssim_floor: float = 0.85,
    initial_params: Optional[TraceParams] = None,
    work_dir: Optional[str] = None,
    render_density: int = 150,
) -> Dict[str, Any]:
    """Run the iterative convergence loop to refine a photo-to-vector illustration.

    Returns a dict with final metrics: global_ssim, iterations, accepted, rejected,
    regions_converged, and the output_path.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source image not found: {source_path}")

    if initial_params is None:
        initial_params = DEFAULT_INITIAL_PARAMS

    cleanup_workdir = False
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="refine_")
        cleanup_workdir = True

    checkpoint_dir = os.path.join(work_dir, "checkpoints")
    checkpoints = CheckpointManager(checkpoint_dir)

    # Per-region state tracking
    region_retries: Dict[tuple, int] = {}
    converged_regions: set = set()
    # Per-region params (start with initial for all)
    region_params: Dict[tuple, TraceParams] = {}

    stats = {
        "iterations": 0,
        "accepted": 0,
        "rejected": 0,
        "regions_converged": 0,
        "global_ssim": 0.0,
        "output_path": output_path,
    }

    try:
        source_img = load_image(source_path)
        h, w = source_img.shape[:2]

        # Phase 1: Initial coarse trace
        logging.info("Phase 1: Initial coarse trace...")
        trace_dir = os.path.join(work_dir, "initial_trace")
        os.makedirs(trace_dir, exist_ok=True)

        svg_elem = trace_image(source_img, initial_params, work_dir=trace_dir)
        current_svg = os.path.join(work_dir, "current.svg")
        write_svg(svg_elem, current_svg)

        # Render and compute baseline SSIM
        render_path = os.path.join(work_dir, "render.png")
        render_svg(current_svg, render_path, density=render_density)
        render_img = load_image(render_path)

        # Resize render to match source if dimensions differ (magick may change size)
        if render_img.shape[:2] != source_img.shape[:2]:
            import cv2
            render_img = cv2.resize(render_img, (w, h))

        current_global_ssim = compute_ssim(source_img, render_img)
        checkpoints.save(current_svg)

        logging.info(f"Baseline global SSIM: {current_global_ssim:.4f}")

        # Phase 2: Iterative refinement
        logging.info("Phase 2: Iterative refinement loop...")
        consecutive_rejections = 0

        for iteration in range(max_iterations):
            stats["iterations"] = iteration + 1
            iter_prefix = f"Iteration {iteration + 1}/{max_iterations}"

            # Compute SSIM grid
            scores = ssim_grid(source_img, render_img, grid=grid)
            r, c, worst_score = worst_region(scores)

            logging.info(
                f"{iter_prefix}: global_ssim={current_global_ssim:.4f}, "
                f"worst_region=({r},{c}) ssim={worst_score:.4f}"
            )

            # Check convergence conditions
            if current_global_ssim >= target_ssim:
                logging.info(
                    f"{iter_prefix}: Target SSIM {target_ssim} reached. Converged."
                )
                break

            if worst_score >= region_ssim_floor:
                logging.info(
                    f"{iter_prefix}: All regions above SSIM floor {region_ssim_floor}. Converged."
                )
                break

            # Skip converged regions — find next worst
            if (r, c) in converged_regions:
                # Find next worst non-converged region
                found = False
                flat_indices = scores.flatten().argsort()
                for idx in flat_indices:
                    ri, ci = divmod(idx, grid)
                    if (ri, ci) not in converged_regions:
                        r, c = ri, ci
                        worst_score = float(scores[r, c])
                        found = True
                        break
                if not found:
                    logging.info(f"{iter_prefix}: All regions converged.")
                    break

            # Get or initialize region state
            region_key = (r, c)
            if region_key not in region_retries:
                region_retries[region_key] = 0
                region_params[region_key] = TraceParams(**asdict(initial_params))

            # Check retry budget
            if region_retries[region_key] >= max_retries_per_region:
                converged_regions.add(region_key)
                stats["regions_converged"] = len(converged_regions)
                logging.info(
                    f"{iter_prefix}: Region ({r},{c}) retry budget exhausted. Marking converged."
                )
                continue

            # Crop source and render for VLM diagnosis
            source_crop, x_off, y_off, tw, th = crop_region(source_img, r, c, grid)
            render_crop, _, _, _, _ = crop_region(render_img, r, c, grid)

            source_crop_path = os.path.join(work_dir, "source_crop.png")
            render_crop_path = os.path.join(work_dir, "render_crop.png")
            save_image(source_crop, source_crop_path)
            save_image(render_crop, render_crop_path)

            # VLM diagnosis (GPU)
            logging.info(f"{iter_prefix}: VLM diagnosing region ({r},{c})...")
            try:
                diagnosis = diagnose_region(
                    source_crop_path, render_crop_path, model=vlm_model
                )
                logging.info(f"{iter_prefix}: VLM diagnosis: {diagnosis[:200]}...")
            except (RuntimeError, Exception) as e:
                logging.warning(f"{iter_prefix}: VLM diagnosis failed: {e}. Skipping iteration.")
                region_retries[region_key] += 1
                consecutive_rejections += 1
                continue

            # LLM parameter prescription (GPU)
            current_params = region_params[region_key]
            logging.info(f"{iter_prefix}: LLM prescribing parameters for region ({r},{c})...")
            try:
                new_params_dict = prescribe_params(
                    diagnosis=diagnosis,
                    current_params=asdict(current_params),
                    current_ssim=worst_score,
                    model=llm_model,
                )
                new_params = TraceParams.from_dict(new_params_dict)
            except (RuntimeError, Exception) as e:
                logging.warning(f"{iter_prefix}: LLM prescription failed: {e}. Skipping iteration.")
                region_retries[region_key] += 1
                consecutive_rejections += 1
                continue

            logging.info(
                f"{iter_prefix}: Prescribed params: n_colors={new_params.n_colors}, "
                f"method={new_params.method}, turdsize={new_params.turdsize}"
            )

            # Re-trace region with new parameters (CPU)
            region_trace_dir = os.path.join(work_dir, f"region_{r}_{c}")
            os.makedirs(region_trace_dir, exist_ok=True)
            region_svg = trace_image(source_crop, new_params, work_dir=region_trace_dir)

            # Patch into SVG candidate
            candidate_svg = os.path.join(work_dir, "candidate.svg")
            patch_region(
                current_svg, region_svg, r, c, grid, w, h, candidate_svg
            )

            # Render candidate and compute new SSIM
            candidate_render_path = os.path.join(work_dir, "candidate_render.png")
            render_svg(candidate_svg, candidate_render_path, density=render_density)
            candidate_render = load_image(candidate_render_path)

            if candidate_render.shape[:2] != source_img.shape[:2]:
                import cv2
                candidate_render = cv2.resize(candidate_render, (w, h))

            new_global_ssim = compute_ssim(source_img, candidate_render)
            new_region_crop, _, _, _, _ = crop_region(candidate_render, r, c, grid)
            new_region_ssim = compute_ssim(source_crop, new_region_crop)

            # Quality gate
            if accept_change(
                current_global_ssim, new_global_ssim,
                worst_score, new_region_ssim
            ):
                # ACCEPT
                shutil.copy2(candidate_svg, current_svg)
                render_img = candidate_render
                current_global_ssim = new_global_ssim
                region_params[region_key] = new_params
                checkpoints.save(current_svg)
                stats["accepted"] += 1
                consecutive_rejections = 0
                logging.info(
                    f"{iter_prefix}: ACCEPTED: global_ssim {current_global_ssim:.4f} "
                    f"(+{new_global_ssim - current_global_ssim + GATE_EPSILON:.4f}), "
                    f"region_ssim {new_region_ssim:.4f}"
                )
            elif is_marginal(current_global_ssim, new_global_ssim):
                # Marginal — try VLM tiebreaker
                logging.info(f"{iter_prefix}: Marginal improvement. Invoking VLM tiebreaker...")
                before_render_path = os.path.join(work_dir, "before_render.png")
                save_image(
                    crop_region(render_img, r, c, grid)[0], before_render_path
                )
                after_render_path = os.path.join(work_dir, "after_render.png")
                save_image(new_region_crop, after_render_path)

                try:
                    choice = tiebreak(
                        source_crop_path, before_render_path,
                        after_render_path, model=vlm_model
                    )
                except Exception:
                    choice = "A"

                if choice == "B":
                    shutil.copy2(candidate_svg, current_svg)
                    render_img = candidate_render
                    current_global_ssim = new_global_ssim
                    region_params[region_key] = new_params
                    checkpoints.save(current_svg)
                    stats["accepted"] += 1
                    consecutive_rejections = 0
                    logging.info(f"{iter_prefix}: Tiebreaker chose B (new). ACCEPTED.")
                else:
                    region_retries[region_key] += 1
                    stats["rejected"] += 1
                    consecutive_rejections += 1
                    logging.info(f"{iter_prefix}: Tiebreaker chose A (current). REJECTED.")
            else:
                # REJECT
                region_retries[region_key] += 1
                stats["rejected"] += 1
                consecutive_rejections += 1
                logging.info(
                    f"{iter_prefix}: REJECTED: global_ssim would be {new_global_ssim:.4f} "
                    f"(delta={new_global_ssim - current_global_ssim:.4f})"
                )

            # Check for stall
            if consecutive_rejections >= max_retries_per_region * 2:
                logging.info(
                    f"{iter_prefix}: {consecutive_rejections} consecutive rejections. "
                    f"Pipeline likely converged."
                )
                break

        # Write final output
        shutil.copy2(current_svg, output_path)
        stats["global_ssim"] = current_global_ssim
        stats["regions_converged"] = len(converged_regions)

        logging.info(
            f"Refinement complete: {stats['iterations']} iterations, "
            f"{stats['accepted']} accepted, {stats['rejected']} rejected, "
            f"final global_ssim={current_global_ssim:.4f}"
        )

        return stats

    finally:
        if cleanup_workdir and os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
