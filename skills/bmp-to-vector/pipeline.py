"""Top-level orchestrator for the photo-to-vector illustration pipeline.

Provides CLI entry point and programmatic API for single-pass tracing
(Architecture A) and iterative refinement (Architecture B).
"""

import argparse
import logging
import os
import sys

from trace import trace_image, write_svg, TraceParams, extract_n_colors_from_svg
from render import load_image
from refine import refine, DEFAULT_INITIAL_PARAMS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


def run_single_pass(
    input_path: str,
    output_path: str,
    n_colors: int = 16,
    method: str = "potrace",
    turdsize: int = 2,
    alphamax: float = 1.0,
    opttolerance: float = 0.2,
    epsilon: float = 2.0,
    morph_kernel: int = 3,
) -> str:
    """Run Architecture A: single-pass color-stratified tracing.

    Returns the output SVG path.
    """
    img = load_image(input_path)

    params = TraceParams(
        n_colors=n_colors,
        turdsize=turdsize,
        alphamax=alphamax,
        opttolerance=opttolerance,
        method=method,
        epsilon=epsilon,
        morph_kernel=morph_kernel,
    )

    svg = trace_image(img, params)
    write_svg(svg, output_path)
    logging.info(f"Single-pass trace complete: {output_path}")
    return output_path


def run_iterative(
    input_path: str,
    output_path: str,
    vlm_model: str = "gemma3:4b",
    llm_model: str = "qwen3.5:4b",
    grid: int = 4,
    max_iterations: int = 20,
    max_retries: int = 3,
    target_ssim: float = 0.92,
    n_colors: int = 12,
    method: str = "potrace",
) -> dict:
    """Run Architecture B: iterative convergence with VLM/LLM guidance.

    Returns stats dict with final metrics.
    """
    initial_params = TraceParams(
        n_colors=n_colors,
        turdsize=5,
        alphamax=1.0,
        opttolerance=0.3,
        method=method,
        epsilon=2.0,
        morph_kernel=3,
    )

    return refine(
        source_path=input_path,
        output_path=output_path,
        vlm_model=vlm_model,
        llm_model=llm_model,
        grid=grid,
        max_iterations=max_iterations,
        max_retries_per_region=max_retries,
        target_ssim=target_ssim,
        initial_params=initial_params,
    )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Photo-to-vector illustration pipeline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single-pass subcommand
    sp = subparsers.add_parser(
        "trace",
        help="Single-pass color-stratified tracing (Architecture A).",
    )
    sp.add_argument("input", help="Path to input image (BMP, PNG, JPG).")
    sp.add_argument("output", help="Path to output SVG file.")
    sp.add_argument("-n", "--n-colors", type=int, default=16,
                    help="Number of color clusters (default: 16).")
    sp.add_argument("-m", "--method", choices=["potrace", "contours"],
                    default="potrace", help="Tracing method (default: potrace).")
    sp.add_argument("-t", "--turdsize", type=int, default=2,
                    help="Noise suppression (default: 2).")
    sp.add_argument("-a", "--alphamax", type=float, default=1.0,
                    help="Corner threshold (default: 1.0).")
    sp.add_argument("-O", "--opttolerance", type=float, default=0.2,
                    help="Curve optimization tolerance (default: 0.2).")
    sp.add_argument("-e", "--epsilon", type=float, default=2.0,
                    help="Path simplification epsilon (default: 2.0).")
    sp.add_argument("-k", "--morph-kernel", type=int, default=3,
                    help="Morphological kernel size, 0 to disable (default: 3).")

    # Iterative refinement subcommand
    rp = subparsers.add_parser(
        "refine",
        help="Iterative convergence refinement (Architecture B).",
    )
    rp.add_argument("input", help="Path to input image (BMP, PNG, JPG).")
    rp.add_argument("output", help="Path to output SVG file.")
    rp.add_argument("--vlm-model", default="gemma3:4b",
                    help="Ollama VLM model for diagnosis (default: gemma3:4b).")
    rp.add_argument("--llm-model", default="qwen3.5:4b",
                    help="Ollama LLM model for parameter prescription (default: qwen3.5:4b).")
    rp.add_argument("--grid", type=int, default=4,
                    help="SSIM grid size (default: 4).")
    rp.add_argument("--max-iterations", type=int, default=20,
                    help="Maximum refinement iterations (default: 20).")
    rp.add_argument("--max-retries", type=int, default=3,
                    help="Max retries per region before marking converged (default: 3).")
    rp.add_argument("--target-ssim", type=float, default=0.92,
                    help="Target global SSIM for convergence (default: 0.92).")
    rp.add_argument("-n", "--n-colors", type=int, default=None,
                    help="Initial number of color clusters (default: 12, or auto-detected from output SVG).")
    rp.add_argument("-m", "--method", choices=["potrace", "contours"],
                    default="potrace", help="Initial tracing method (default: potrace).")

    args = parser.parse_args()

    if args.command == "trace":
        run_single_pass(
            args.input, args.output,
            n_colors=args.n_colors,
            method=args.method,
            turdsize=args.turdsize,
            alphamax=args.alphamax,
            opttolerance=args.opttolerance,
            epsilon=args.epsilon,
            morph_kernel=args.morph_kernel,
        )
    elif args.command == "refine":
        n_colors = args.n_colors
        if n_colors is None:
            detected = extract_n_colors_from_svg(args.output)
            if detected is not None:
                logging.info(
                    f"Auto-detected {detected} colors from existing SVG: {args.output}"
                )
                n_colors = detected
            else:
                n_colors = 12

        stats = run_iterative(
            args.input, args.output,
            vlm_model=args.vlm_model,
            llm_model=args.llm_model,
            grid=args.grid,
            max_iterations=args.max_iterations,
            max_retries=args.max_retries,
            target_ssim=args.target_ssim,
            n_colors=n_colors,
            method=args.method,
        )
        logging.info(f"Final stats: {stats}")


if __name__ == "__main__":
    main()
