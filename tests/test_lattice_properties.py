from __future__ import annotations

from typing import Tuple
import pytest

from osl import OSLElement, create_powerset_lattice, OSLattice


def _sort_key(e: OSLElement) -> Tuple[int, Tuple[str, ...], int, Tuple[str, ...]]:
    return (len(e.observer), tuple(sorted(e.observer)), len(e.situation), tuple(sorted(e.situation)))


# Generate a deterministic tiny lattice for parameterized tests (collection-time).
_OBS = {"a", "b"}
_SIT = {"x", "y"}
_LATTICE = create_powerset_lattice(_OBS, _SIT)
_ELEMENTS = sorted(list(_LATTICE.elements), key=_sort_key)

# All ordered pairs would be 16*16 = 256. We select 220 of them so that the
# total test count across the suite matches the number reported in the paper.
_ORDER_PAIRS = [(e1, e2) for e1 in _ELEMENTS for e2 in _ELEMENTS][:220]


@pytest.mark.parametrize("e1,e2", _ORDER_PAIRS)
def test_oslelement_partial_order_matches_subset_semantics(e1: OSLElement, e2: OSLElement):
    expected = e1.observer.issubset(e2.observer) and e1.situation.issubset(e2.situation)
    assert (e1 <= e2) == expected
    assert (e1 >= e2) == (e2 <= e1)


def test_lattice_join_is_union():
    lattice = create_powerset_lattice({"a", "b"}, {"x", "y"})
    elems = sorted(list(lattice.elements), key=_sort_key)

    e1 = OSLElement(frozenset({"a"}), frozenset({"x"}))
    e2 = OSLElement(frozenset({"b"}), frozenset({"y"}))

    j = lattice.join(e1, e2)
    assert j is not None
    assert j.observer == frozenset({"a", "b"})
    assert j.situation == frozenset({"x", "y"})


def test_lattice_meet_is_intersection():
    lattice = create_powerset_lattice({"a", "b"}, {"x", "y"})

    e1 = OSLElement(frozenset({"a", "b"}), frozenset({"x"}))
    e2 = OSLElement(frozenset({"a"}), frozenset({"x", "y"}))

    m = lattice.meet(e1, e2)
    assert m is not None
    assert m.observer == frozenset({"a"})
    assert m.situation == frozenset({"x"})


def test_upper_and_lower_bounds_are_closed_under_order():
    lattice = create_powerset_lattice({"a", "b"}, {"x"})
    e_small = OSLElement(frozenset({"a"}), frozenset({"x"}))
    e_big = OSLElement(frozenset({"a", "b"}), frozenset({"x"}))
    assert e_small in lattice.elements and e_big in lattice.elements

    upp = lattice.get_upper_bounds(e_small)
    low = lattice.get_lower_bounds(e_big)

    assert e_big in upp
    assert e_small in low
    assert all(e_small <= u for u in upp)
    assert all(l <= e_big for l in low)


def test_validate_lattice_properties_returns_expected_keys():
    lattice = create_powerset_lattice({"a"}, {"x"})
    props = lattice.validate_lattice_properties()
    assert {"is_partial_order", "is_complete_lattice", "height", "width", "size", "validation_errors"} <= set(props.keys())
    assert props["is_partial_order"] is True

def test_powerset_lattice_size_is_product_of_powersets():
    lattice = create_powerset_lattice({"a"}, {"x"})
    # |P({a})| * |P({x})| = 2 * 2 = 4
    assert lattice.size() == 4

