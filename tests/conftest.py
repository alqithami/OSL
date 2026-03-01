from __future__ import annotations

from pathlib import Path
import sys
from typing import List, Tuple

import pytest

# Allow running tests without installing the package
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from osl import OSLElement, create_powerset_lattice  # noqa: E402


@pytest.fixture(scope="session")
def tiny_domain():
    observers = {"a", "b"}
    situations = {"x", "y"}
    return observers, situations


@pytest.fixture(scope="session")
def tiny_lattice(tiny_domain):
    observers, situations = tiny_domain
    return create_powerset_lattice(observers, situations)


@pytest.fixture(scope="session")
def tiny_elements_sorted(tiny_lattice) -> List[OSLElement]:
    def key(e: OSLElement) -> Tuple[int, Tuple[str, ...], int, Tuple[str, ...]]:
        return (len(e.observer), tuple(sorted(e.observer)), len(e.situation), tuple(sorted(e.situation)))

    return sorted(list(tiny_lattice.elements), key=key)
