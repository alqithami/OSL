"""
Command-line interface for the OSL repository.

The paper describes a "single command-line interface" to reproduce experiments.
In this repository you can either:

- Call the experiment runner directly:
    python experiments/run.py --help

- Or use this wrapper (recommended once installed editable):
    osl experiments --help
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _find_repo_root(start: Path) -> Optional[Path]:
    """Find the repository root by walking upwards until we see pyproject.toml."""
    cur = start.resolve()
    for _ in range(10):
        if (cur / "pyproject.toml").exists() or (cur / "setup.py").exists():
            return cur
        cur = cur.parent
    return None


def _run_python_script(script_path: Path, script_args: list[str]) -> int:
    env = os.environ.copy()
    # Make matplotlib safe in headless contexts (CI/Docker)
    env.setdefault("MPLBACKEND", "Agg")
    cmd = [sys.executable, str(script_path), *script_args]
    return subprocess.call(cmd, env=env)


def cmd_experiments(args: argparse.Namespace) -> int:
    repo_root = _find_repo_root(Path.cwd())
    if repo_root is None:
        repo_root = _find_repo_root(Path(__file__).resolve())

    if repo_root is None:
        print("ERROR: Could not locate repository root (pyproject.toml/setup.py).", file=sys.stderr)
        return 2

    script = repo_root / "experiments" / "run.py"
    if not script.exists():
        print(f"ERROR: {script} not found. Run from the repository checkout.", file=sys.stderr)
        return 2

    script_args: list[str] = []
    if args.output_dir:
        script_args += ["--output-dir", args.output_dir]
    if args.quick:
        script_args += ["--quick"]
    if args.experiment:
        script_args += ["--experiment", args.experiment]

    return _run_python_script(script, script_args)


def cmd_tom(args: argparse.Namespace) -> int:
    repo_root = _find_repo_root(Path.cwd())
    if repo_root is None:
        repo_root = _find_repo_root(Path(__file__).resolve())

    if repo_root is None:
        print("ERROR: Could not locate repository root (pyproject.toml/setup.py).", file=sys.stderr)
        return 2

    script = repo_root / "experiments" / "tom_suite.py"
    if not script.exists():
        print(f"ERROR: {script} not found. Run from the repository checkout.", file=sys.stderr)
        return 2

    script_args: list[str] = []
    if args.output:
        script_args += ["--output", args.output]
    if args.print_table:
        script_args += ["--print-table"]

    return _run_python_script(script, script_args)


def cmd_test(args: argparse.Namespace) -> int:
    # Prefer pytest if available
    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")

    if args.pytest:
        cmd = [sys.executable, "-m", "pytest", "-q"]
        if args.coverage:
            cmd += ["--cov=osl", "--cov-report=term-missing", "--cov-branch"]
        return subprocess.call(cmd, env=env)

    # Fallback: run unittest (legacy)
    cmd = [sys.executable, "-m", "unittest", "discover", "-v"]
    return subprocess.call(cmd, env=env)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="osl", description="OSL repository command-line interface")
    sub = parser.add_subparsers(dest="command", required=True)

    p_exp = sub.add_parser("experiments", help="Run experiment suite (baseline/scalability/ablation/correctness)")
    p_exp.add_argument("--experiment", choices=["all", "baseline", "scalability", "ablation", "correctness"], default="all")
    p_exp.add_argument("--quick", action="store_true", help="Run the quick configuration (CI-friendly).")
    p_exp.add_argument("--output-dir", default="results", help="Directory to write results and figures.")
    p_exp.set_defaults(func=cmd_experiments)

    p_tom = sub.add_parser("tom", help="Run Theory-of-Mind scenario suite (Table 3).")
    p_tom.add_argument("--output", default="results_full/tom_suite_results.json", help="Where to save JSON results.")
    p_tom.add_argument("--print-table", action="store_true", help="Print a Markdown table to stdout.")
    p_tom.set_defaults(func=cmd_tom)

    p_test = sub.add_parser("test", help="Run tests (pytest recommended).")
    p_test.add_argument("--pytest", action="store_true", help="Use pytest (default).")
    p_test.add_argument("--coverage", action="store_true", help="Enable coverage reporting (pytest only).")
    p_test.set_defaults(func=cmd_test, pytest=True)

    ns = parser.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    raise SystemExit(main())
