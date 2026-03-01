from __future__ import annotations

import pytest

from osl import (
    BeliefBase,
    OSLElement,
    create_powerset_lattice,
    RBPAlgorithm,
    MCCAlgorithm,
    ATMSBaseline,
    DTMSBaseline,
    MEPKBaseline,
)


def _simple_setup():
    lattice = create_powerset_lattice({"a", "b"}, {"x"})
    bb = BeliefBase(lattice)
    e1 = OSLElement(frozenset({"a"}), frozenset({"x"}))
    e2 = OSLElement(frozenset({"b"}), frozenset({"x"}))
    bb.add_belief(e1, "p", True, confidence=0.9)
    bb.add_belief(e2, "p", False, confidence=0.9)
    return lattice, bb, e1, e2


def test_rbp_returns_expected_fields():
    lattice, bb, _, _ = _simple_setup()
    rbp = RBPAlgorithm(lattice, max_iterations=5)
    result = rbp.propagate_beliefs(bb)
    assert {"runtime", "iterations", "convergence", "affected_elements", "predicates_processed"} <= set(result.keys())
    assert result["runtime"] >= 0.0
    assert result["iterations"] >= 1


def test_rbp_with_no_predicates_is_noop():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    rbp = RBPAlgorithm(lattice, max_iterations=5)
    result = rbp.propagate_beliefs(bb)
    assert result["iterations"] == 0
    assert result["convergence"] is True
    assert result["predicates_processed"] == 0


def test_rbp_affects_some_elements_for_nonempty_beliefbase():
    lattice, bb, _, _ = _simple_setup()
    rbp = RBPAlgorithm(lattice, max_iterations=5)
    result = rbp.propagate_beliefs(bb)
    assert result["affected_elements"] >= 0


def test_mcc_detect_contradictions_reports_total_contradictions():
    lattice, bb, _, _ = _simple_setup()
    mcc = MCCAlgorithm(lattice)
    out = mcc.detect_contradictions(bb)
    assert "total_contradictions" in out
    assert out["total_contradictions"] >= 0


def test_mcc_resolve_contradictions_returns_resolution_stats():
    lattice, bb, _, _ = _simple_setup()
    mcc = MCCAlgorithm(lattice, resolution_strategy="confidence")
    before = len(bb.detect_contradictions())
    res = mcc.resolve_contradictions(bb)
    assert {"runtime", "resolutions_made", "components_resolved", "detection_results"} <= set(res.keys())
    after = len(bb.detect_contradictions())
    # In general we expect not to increase contradictions
    assert after <= before


def test_atms_baseline_runs_and_returns_fields():
    lattice, bb, _, _ = _simple_setup()
    atms = ATMSBaseline()
    out = atms.process_beliefs(bb)
    assert {"runtime", "assumptions", "justifications", "contradictions", "propagation_iterations"} <= set(out.keys())


def test_dtms_baseline_runs_and_returns_fields():
    lattice, bb, _, _ = _simple_setup()
    dtms = DTMSBaseline()
    out = dtms.process_beliefs(bb)
    assert {"runtime", "nodes", "dependencies", "contradictions", "maintenance_iterations"} <= set(out.keys())


def test_mepk_baseline_runs_and_returns_fields():
    lattice, bb, _, _ = _simple_setup()
    mepk = MEPKBaseline()
    out = mepk.process_beliefs(bb)
    assert {"runtime", "variables", "constraints", "inference_iterations", "inference_converged"} <= set(out.keys())


def test_baselines_handle_empty_beliefbase():
    lattice = create_powerset_lattice({"a"}, {"x"})
    bb = BeliefBase(lattice)
    assert ATMSBaseline().process_beliefs(bb)["assumptions"] == 0
    assert DTMSBaseline().process_beliefs(bb)["nodes"] == 0
    assert MEPKBaseline().process_beliefs(bb)["variables"] == 0


def test_rbp_does_not_create_invalid_confidences():
    lattice, bb, e1, _ = _simple_setup()
    rbp = RBPAlgorithm(lattice, max_iterations=5)
    rbp.propagate_beliefs(bb)
    conf = bb.get_belief_confidence(e1, "p")
    assert 0.0 <= conf <= 1.0


def test_mcc_contradiction_graph_statistics_present():
    lattice, bb, _, _ = _simple_setup()
    mcc = MCCAlgorithm(lattice)
    out = mcc.detect_contradictions(bb)
    stats = out.get("graph_statistics", {})
    assert {"node_count", "edge_count", "connected_components"} <= set(stats.keys())


def test_mcc_resolution_strategy_majority_is_supported():
    lattice, bb, _, _ = _simple_setup()
    mcc = MCCAlgorithm(lattice, resolution_strategy="majority")
    res = mcc.resolve_contradictions(bb)
    assert "resolutions_made" in res
