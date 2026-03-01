from __future__ import annotations

import pytest

from osl import Belief, BeliefBase, OSLElement, create_powerset_lattice


def test_belief_confidence_must_be_in_unit_interval():
    with pytest.raises(ValueError):
        Belief(predicate="p", value=True, confidence=1.5)


def test_boolean_beliefs_contradict_when_values_differ():
    b1 = Belief("p", True, confidence=1.0)
    b2 = Belief("p", False, confidence=1.0)
    assert b1.is_contradictory(b2) is True


def test_numeric_beliefs_use_tolerance_for_contradiction():
    b1 = Belief("temp", 1.0, confidence=1.0)
    b2 = Belief("temp", 1.05, confidence=1.0)
    b3 = Belief("temp", 1.2, confidence=1.0)
    assert b1.is_contradictory(b2) is False  # within tolerance
    assert b1.is_contradictory(b3) is True   # outside tolerance


def test_string_beliefs_contradict_when_values_differ():
    b1 = Belief("loc", "basket", confidence=1.0)
    b2 = Belief("loc", "box", confidence=1.0)
    assert b1.is_contradictory(b2) is True


def test_beliefbase_returns_highest_confidence_value():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    e = OSLElement(frozenset({"a"}), frozenset({"x"}))

    bb.add_belief(e, "p", "v1", confidence=0.4)
    bb.add_belief(e, "p", "v2", confidence=0.9)

    assert bb.get_belief_value(e, "p") == "v2"
    assert bb.get_belief_confidence(e, "p") == pytest.approx(0.9)


def test_beliefbase_rejects_contradictory_belief_on_same_element():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    e = OSLElement(frozenset({"a"}), frozenset({"x"}))

    assert bb.add_belief(e, "p", True, confidence=0.9) is True
    # Equal-confidence contradiction is rejected (see BeliefBase.add_belief policy)
    assert bb.add_belief(e, "p", False, confidence=0.9) is False
    assert len(bb.contradictions) >= 1

    # Higher-confidence contradiction replaces the existing belief
    assert bb.add_belief(e, "p", False, confidence=0.95) is True
    assert bb.get_belief_value(e, "p") is False
    assert bb.get_belief_confidence(e, "p") == pytest.approx(0.95)
def test_beliefbase_detects_contradiction_across_comparable_elements():
    lattice = create_powerset_lattice({"a", "b"}, {"x"})
    bb = BeliefBase(lattice)

    e_small = OSLElement(frozenset({"a"}), frozenset({"x"}))
    e_big = OSLElement(frozenset({"a", "b"}), frozenset({"x"}))

    bb.add_belief(e_small, "p", "v1", confidence=1.0)
    bb.add_belief(e_big, "p", "v2", confidence=1.0)

    contradictions = bb.detect_contradictions()
    assert any(c[0] == e_small or c[2] == e_small for c in contradictions)


def test_beliefbase_get_all_predicates_tracks_insertions():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    e = OSLElement(frozenset({"a"}), frozenset({"x"}))

    bb.add_belief(e, "p1", True, confidence=1.0)
    bb.add_belief(e, "p2", False, confidence=1.0)

    preds = bb.get_all_predicates()
    assert {"p1", "p2"} <= preds


def test_beliefbase_size_counts_total_beliefs():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    e = OSLElement(frozenset({"a"}), frozenset({"x"}))

    assert bb.size() == 0
    bb.add_belief(e, "p", True, confidence=1.0)
    bb.add_belief(e, "q", "x", confidence=1.0)
    assert bb.size() == 2


def test_beliefbase_get_belief_value_none_when_absent():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    e = OSLElement(frozenset({"a"}), frozenset({"x"}))
    assert bb.get_belief_value(e, "missing") is None
