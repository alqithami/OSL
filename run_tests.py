#!/usr/bin/env python3
"""
Test runner for the OSL repository.

Default:
  python run_tests.py

With coverage:
  python run_tests.py --coverage

Stress tests (not run by default):
  python run_tests.py --stress
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OSL test suite.")
    parser.add_argument("--coverage", action="store_true", help="Enable coverage reporting (pytest-cov).")
    parser.add_argument("--stress", action="store_true", help="Run stress tests (marked 'stress').")
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")

    cmd = [sys.executable, "-m", "pytest", "-q"]
    if args.coverage:
        cmd += ["--cov=osl", "--cov-report=term-missing", "--cov-branch"]
    if args.stress:
        cmd += ["-m", "stress"]
    else:
        cmd += ["-m", "not stress"]

    return subprocess.call(cmd, cwd=REPO_ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
