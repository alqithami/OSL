#!/usr/bin/env python3
"""
Reproduce the experiments reported in the OSL paper.

Paper:
  Saad Alqithami. 2026. The Observer–Situation Lattice: A Unified Formal Basis for
  Perspective-Aware Cognition. Proc. of AAMAS 2026, Paphos, Cyprus.
  DOI: 10.65109/CHZG9392

This script runs the full experimental suite and writes outputs to `results_full/`:
- Table 1 + Figure 3: baseline comparison (OSL vs ATMS/DTMS/MEPK)
- Table 2: scalability + ablation study
- Table 3: Theory-of-Mind scenario suite
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def _run(cmd: list[str]) -> None:
    print("  $", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, check=True, env={**dict(**__import__("os").environ), "MPLBACKEND": "Agg"})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full OSL paper experimental suite.")
    parser.add_argument("--output-dir", default="results_full", help="Directory for outputs (default: results_full).")
    parser.add_argument("--quick", action="store_true", help="Run a quick configuration (for CI/sanity checks).")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    print("🚀 OSL – Full Experimental Suite")
    print(f"Output directory: {out_dir}")
    print("=" * 72)

    # Core experiment runner (Tables 1–2 + Figures)
    exp_cmd = [sys.executable, "experiments/run.py", "--output-dir", str(out_dir)]
    if args.quick:
        exp_cmd.append("--quick")

    # ToM suite (Table 3)
    tom_cmd = [
        sys.executable,
        "experiments/tom_suite.py",
        "--output",
        str(out_dir / "tom_suite_results.json"),
    ]

    try:
        print("\n[1/2] Running main experiment suite (scalability/baselines/ablation/correctness)")
        _run(exp_cmd)

        print("\n[2/2] Running Theory-of-Mind suite (Table 3)")
        _run(tom_cmd)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Experimental suite failed (exit code {e.returncode}).")
        return int(e.returncode)

    elapsed = time.time() - start
    print("\n✅ Done.")
    print(f"Total wall time: {elapsed:.2f}s")
    print(f"Outputs written to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
