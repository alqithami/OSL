from __future__ import annotations

import math
import random
import time

import pytest

from osl import OSLElement, OSLattice, BeliefBase


def _balanced_lattice(target_elements: int) -> OSLattice:
    """
    Create ~target_elements lattice elements without building huge observer/situation sets.

    This mirrors the "mixed lattice structure" used in the experiment generator:
    - observer sets grow up to O(sqrt(n))
    - situation sets remain small (singleton), keeping memory practical.
    """
    lattice = OSLattice()
    chain_len = int(math.sqrt(target_elements))
    chain_len = max(chain_len, 2)
    width = max(target_elements // chain_len, 2)

    # Precompute observers progressively to avoid repeated allocations.
    obs_prefix: list[str] = []
    for i in range(chain_len):
        obs_prefix.append(f"obs{i}")
        obs_set = frozenset(obs_prefix)
        for j in range(width):
            sit_set = frozenset([f"sit{j}"])
            lattice.add_element(OSLElement(obs_set, sit_set))

    return lattice


@pytest.mark.stress
def test_stress_large_lattice_construction_1e5_elements():
    t0 = time.perf_counter()
    lattice = _balanced_lattice(100_000)
    t1 = time.perf_counter()

    # The generator is approximate; allow some slack.
    assert lattice.size() >= 90_000
    assert (t1 - t0) >= 0.0  # just ensure it ran


@pytest.mark.stress
def test_stress_belief_insertion_1e4_simultaneous():
    lattice = _balanced_lattice(100_000)
    bb = BeliefBase(lattice)

    elements = list(lattice.elements)
    random.seed(0)

    t0 = time.perf_counter()
    for k in range(10_000):
        e = elements[random.randrange(len(elements))]
        bb.add_belief(e, predicate=f"p{k % 50}", value=(k % 3), confidence=0.5)
    t1 = time.perf_counter()

    assert bb.size() == 10_000
    assert (t1 - t0) >= 0.0
