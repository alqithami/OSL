"""Setup script for the OSL (Observer–Situation Lattice) framework.

This repository accompanies the paper:

Saad Alqithami. 2026. *The Observer–Situation Lattice: A Unified Formal Basis for
Perspective-Aware Cognition*. Proc. of the 25th International Conference on
Autonomous Agents and Multiagent Systems (AAMAS 2026), Paphos, Cyprus.
DOI: 10.65109/CHZG9392
"""

from setuptools import setup, find_packages
from pathlib import Path

ROOT = Path(__file__).parent


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_requirements(path: str) -> list[str]:
    reqs = []
    for line in read_text(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        reqs.append(line)
    return reqs


setup(
    name="osl-framework",
    version="1.0.0",
    description="Observer–Situation Lattice (OSL): perspective-aware belief management and reasoning",
    long_description=read_text("README.md"),
    long_description_content_type="text/markdown",
    author="Saad Alqithami",
    author_email="salqithami@bu.edu.sa",
    url="https://github.com/alqithami/OSL",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=read_requirements("requirements.txt"),
    extras_require={"dev": read_requirements("requirements-dev.txt")},
    entry_points={"console_scripts": ["osl=osl.cli:main"]},
    include_package_data=True,
)
