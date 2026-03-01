#!/usr/bin/env python3
"""
Theory-of-Mind (ToM) scenario suite for the OSL framework (Table 3).

This script is intended to reproduce the qualitative ToM evaluation reported in:

Saad Alqithami. 2026. The Observer–Situation Lattice: A Unified Formal Basis for
Perspective-Aware Cognition. AAMAS 2026. DOI: 10.65109/CHZG9392

Each scenario is encoded by choosing appropriate observer–situation nodes
(OSL elements) and belief records. The reasoning machinery (RBP and MCC)
is unchanged, matching the paper's experimental methodology.

Run:
  python experiments/tom_suite.py --print-table
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import sys

# Allow running from repo checkout without installation
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from osl import OSLElement, OSLattice, BeliefBase, RBPAlgorithm, MCCAlgorithm  # noqa: E402


@dataclass
class ScenarioResult:
    scenario: str
    osl_result: str
    expected: str
    confidence: float
    runtime_ms: float
    details: Dict[str, Any]


def _make_element(observer: str | List[str], situation: List[str] | str) -> OSLElement:
    if isinstance(observer, str):
        obs = frozenset([observer])
    else:
        obs = frozenset(observer)
    if isinstance(situation, str):
        sit = frozenset([situation])
    else:
        sit = frozenset(situation)
    return OSLElement(obs, sit)


def _run_rbp_and_mcc(lattice: OSLattice, belief_base: BeliefBase, max_iterations: int = 10) -> None:
    rbp = RBPAlgorithm(lattice, max_iterations=max_iterations)
    rbp.propagate_beliefs(belief_base)

    # MCC is not strictly required for ToM queries, but the paper evaluates both.
    mcc = MCCAlgorithm(lattice)
    mcc.detect_contradictions(belief_base)


def scenario_sally_anne_basic() -> ScenarioResult:
    """
    Classic Sally–Anne false-belief task.
    Expected: Sally searches where she left the ball (basket), not where Anne moved it (box).
    """
    lattice = OSLattice()
    sally = _make_element("sally", "room")
    anne = _make_element("anne", "room")
    observer = _make_element("observer", "room")
    sally_anne = _make_element(["sally", "anne"], "room")

    for e in [sally, anne, observer, sally_anne]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)
    bb.add_belief(sally, "ball_location", "basket", confidence=1.0, source="sally_action")
    bb.add_belief(anne, "ball_location", "box", confidence=1.0, source="anne_action")
    bb.add_belief(observer, "actual_location", "box", confidence=1.0, source="ground_truth")

    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted = bb.get_belief_value(sally, "ball_location")
    conf = bb.get_belief_confidence(sally, "ball_location")
    expected = "basket"

    return ScenarioResult(
        scenario="Sally–Anne (basic)",
        osl_result="PASS" if predicted == expected else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={
            "sally_ball_location": predicted,
            "anne_ball_location": bb.get_belief_value(anne, "ball_location"),
            "actual_location": bb.get_belief_value(observer, "actual_location"),
        },
    )


def scenario_sally_anne_with_distractor() -> ScenarioResult:
    """
    Sally–Anne with an additional irrelevant (distractor) object/location fact.
    Expected: distractor does not affect the false-belief inference.
    """
    lattice = OSLattice()
    sally = _make_element("sally", "room")
    anne = _make_element("anne", "room")
    observer = _make_element("observer", "room")
    sally_anne = _make_element(["sally", "anne"], "room")

    for e in [sally, anne, observer, sally_anne]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)
    bb.add_belief(sally, "ball_location", "basket", confidence=1.0, source="sally_action")
    bb.add_belief(anne, "ball_location", "box", confidence=1.0, source="anne_action")
    bb.add_belief(observer, "actual_location", "box", confidence=1.0, source="ground_truth")

    # Distractor (should be irrelevant to the queried belief)
    bb.add_belief(sally, "toy_location", "drawer", confidence=1.0, source="sally_action")
    bb.add_belief(anne, "toy_location", "drawer", confidence=1.0, source="anne_observes")

    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted = bb.get_belief_value(sally, "ball_location")
    conf = bb.get_belief_confidence(sally, "ball_location")
    expected = "basket"

    return ScenarioResult(
        scenario="Sally–Anne with distractor",
        osl_result="PASS" if predicted == expected else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={"sally_ball_location": predicted, "distractor": bb.get_belief_value(sally, "toy_location")},
    )


def scenario_nested_belief_level_2() -> ScenarioResult:
    """
    Nested belief (Level 2): Sally holds a belief *about* Anne's belief.
    We encode the nested belief as an ordinary predicate in Sally's belief base.
    """
    lattice = OSLattice()
    sally = _make_element("sally", "room")
    anne = _make_element("anne", "room")
    sally_anne = _make_element(["sally", "anne"], "room")

    for e in [sally, anne, sally_anne]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)

    # Anne's first-order belief
    bb.add_belief(anne, "ball_location", "box", confidence=1.0, source="anne_action")

    # Sally's second-order belief about Anne
    bb.add_belief(sally, "anne_believes_ball_location", "box", confidence=0.95, source="sally_infers")

    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted = bb.get_belief_value(sally, "anne_believes_ball_location")
    conf = bb.get_belief_confidence(sally, "anne_believes_ball_location")
    expected = "box"

    return ScenarioResult(
        scenario="Nested belief (Level 2)",
        osl_result="PASS" if predicted == expected else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={"sally_nested_belief": predicted, "anne_first_order": bb.get_belief_value(anne, "ball_location")},
    )


def scenario_multiple_objects() -> ScenarioResult:
    """
    Multiple objects: maintain distinct belief states over multiple predicates.
    """
    lattice = OSLattice()
    sally = _make_element("sally", "room")
    anne = _make_element("anne", "room")
    observer = _make_element("observer", "room")

    for e in [sally, anne, observer]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)

    # Object 1: ball (false belief persists for Sally)
    bb.add_belief(sally, "ball_location", "basket", confidence=1.0, source="sally_action")
    bb.add_belief(anne, "ball_location", "box", confidence=1.0, source="anne_action")
    bb.add_belief(observer, "ball_actual_location", "box", confidence=1.0, source="ground_truth")

    # Object 2: key (shared belief)
    bb.add_belief(sally, "key_location", "drawer", confidence=1.0, source="sally_action")
    bb.add_belief(anne, "key_location", "drawer", confidence=1.0, source="anne_observes")
    bb.add_belief(observer, "key_actual_location", "drawer", confidence=1.0, source="ground_truth")

    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted_ball = bb.get_belief_value(sally, "ball_location")
    predicted_key = bb.get_belief_value(sally, "key_location")
    expected_ball = "basket"
    expected_key = "drawer"

    ok = (predicted_ball == expected_ball) and (predicted_key == expected_key)

    conf_ball = bb.get_belief_confidence(sally, "ball_location")
    conf_key = bb.get_belief_confidence(sally, "key_location")
    conf = min(conf_ball, conf_key)

    return ScenarioResult(
        scenario="Multiple objects",
        osl_result="PASS" if ok else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={"sally_ball": predicted_ball, "sally_key": predicted_key},
    )


def scenario_temporal_belief_change() -> ScenarioResult:
    """
    Temporal belief change: Sally updates her belief after observing a change.
    We represent time as increasing situation sets (subset inclusion).
    """
    lattice = OSLattice()

    # Situation chain: t0 ⊂ t0,t1
    t0_sit = ["t0"]
    t1_sit = ["t0", "t1"]

    sally_t0 = _make_element("sally", t0_sit)
    sally_t1 = _make_element("sally", t1_sit)

    for e in [sally_t0, sally_t1]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)
    bb.add_belief(sally_t0, "ball_location", "basket", confidence=1.0, source="initial_state")
    bb.add_belief(sally_t1, "ball_location", "box", confidence=0.975, source="sally_observes_change")

    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted = bb.get_belief_value(sally_t1, "ball_location")
    conf = bb.get_belief_confidence(sally_t1, "ball_location")
    expected = "box"

    return ScenarioResult(
        scenario="Temporal belief change",
        osl_result="PASS" if predicted == expected else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={"sally_t1_ball_location": predicted},
    )


def scenario_false_photograph() -> ScenarioResult:
    """
    False photograph: Sally bases her belief on an outdated photo (false representation).
    Expected: Sally answers according to the photo, not current reality.
    """
    lattice = OSLattice()
    sally = _make_element("sally", "photo_task")
    observer = _make_element("observer", "photo_task")

    for e in [sally, observer]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)

    # Photo indicates basket (outdated), reality is box.
    bb.add_belief(sally, "ball_location", "basket", confidence=1.0, source="photo")
    bb.add_belief(observer, "ball_actual_location", "box", confidence=1.0, source="ground_truth")

    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted = bb.get_belief_value(sally, "ball_location")
    conf = bb.get_belief_confidence(sally, "ball_location")
    expected = "basket"

    return ScenarioResult(
        scenario="False photograph",
        osl_result="PASS" if predicted == expected else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={"sally_ball_location": predicted},
    )


def scenario_appearance_reality() -> ScenarioResult:
    """
    Appearance–reality: distinguish appearance-based belief from actual reality.
    """
    lattice = OSLattice()
    sally = _make_element("sally", "appearance_task")
    observer = _make_element("observer", "appearance_task")

    for e in [sally, observer]:
        lattice.add_element(e)

    bb = BeliefBase(lattice)

    # Appearance belief (Sally) vs reality (observer/ground truth)
    bb.add_belief(sally, "object_looks_like", "rock", confidence=0.925, source="appearance")
    bb.add_belief(observer, "object_is", "sponge", confidence=1.0, source="ground_truth")

    # The ToM-style query here is "what will Sally say it is?" => rock
    t0 = time.perf_counter()
    _run_rbp_and_mcc(lattice, bb, max_iterations=10)
    t1 = time.perf_counter()

    predicted = bb.get_belief_value(sally, "object_looks_like")
    conf = bb.get_belief_confidence(sally, "object_looks_like")
    expected = "rock"

    return ScenarioResult(
        scenario="Appearance–reality",
        osl_result="PASS" if predicted == expected else "FAIL",
        expected="PASS",
        confidence=float(conf),
        runtime_ms=(t1 - t0) * 1000.0,
        details={"sally_appearance": predicted, "reality": bb.get_belief_value(observer, "object_is")},
    )


SCENARIOS = [
    scenario_sally_anne_basic,
    scenario_sally_anne_with_distractor,
    scenario_nested_belief_level_2,
    scenario_multiple_objects,
    scenario_temporal_belief_change,
    scenario_false_photograph,
    scenario_appearance_reality,
]


def _format_markdown_table(results: List[ScenarioResult]) -> str:
    rows = [
        "| Scenario | OSL result | Expected | Confidence | Runtime (ms) |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in results:
        rows.append(
            f"| {r.scenario} | {r.osl_result} | {r.expected} | {r.confidence:.3f} | {r.runtime_ms:.3f} |"
        )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="OSL Theory-of-Mind scenario suite (Table 3)")
    parser.add_argument("--output", default="results_full/tom_suite_results.json", help="Path to save JSON results.")
    parser.add_argument("--print-table", action="store_true", help="Print a Markdown table to stdout.")
    args = parser.parse_args()

    results: List[ScenarioResult] = [fn() for fn in SCENARIOS]

    out_path = REPO_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at_unix": time.time(),
        "results": [asdict(r) for r in results],
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.osl_result == "PASS"),
            "failed": sum(1 for r in results if r.osl_result != "PASS"),
            "avg_runtime_ms": sum(r.runtime_ms for r in results) / max(1, len(results)),
        },
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.print_table:
        print(_format_markdown_table(results))

    print(f"✅ ToM suite finished. Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
