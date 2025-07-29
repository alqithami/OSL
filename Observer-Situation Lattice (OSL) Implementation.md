# Observer-Situation Lattice (OSL) Implementation

**Anonymous Submission - AAAI 2026**

This repository contains the complete implementation and experimental pipeline for the paper "The Observer-Situation Lattice: A Unified Formal Basis for Perspective-Aware Cognition."

## Overview

The Observer-Situation Lattice (OSL) provides a unified algebraic framework for perspective-aware reasoning in artificial intelligence systems. This implementation demonstrates the theoretical claims through comprehensive experiments comparing OSL with state-of-the-art approaches.

## Key Results Reproduced

- **10-50× speedup** over AGM truth maintenance systems
- **Sub-linear scaling** O(√n) for belief updates in balanced lattices  
- **Perfect accuracy** on Theory-of-Mind benchmarks (Sally-Anne, etc.)
- **92% task completion** in multi-agent coordination vs 78% for BDI baselines
- **40% faster context adaptation** compared to rule-based systems

## Repository Structure

```
osl_implementation/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── setup.py                 # Package installation
├── run_all_experiments.py   # Main script to reproduce all results
├── src/                     # Core OSL implementation
│   ├── osl/                 # Main OSL package
│   │   ├── __init__.py
│   │   ├── lattice.py       # Lattice data structures
│   │   ├── belief_base.py   # Belief management
│   │   ├── algorithms.py    # RBP and MCC algorithms
│   │   └── utils.py         # Utility functions
│   └── agent/               # OSL-based agent architecture
│       ├── __init__.py
│       ├── perception.py    # Perception module
│       ├── planning.py      # Planning module
│       └── explanation.py   # Explanation generation
├── experiments/             # Experimental evaluation
│   ├── performance/         # Performance benchmarks
│   ├── theory_of_mind/      # ToM task evaluation
│   ├── multi_agent/         # Multi-agent scenarios
│   └── explanation/         # Explanation quality tests
├── baselines/               # Baseline system implementations
│   ├── bdi_baseline.py      # Jason BDI comparison
│   ├── agm_tms.py          # AGM truth maintenance
│   └── epistemic_planner.py # Epistemic planning baseline
├── data/                    # Generated datasets and benchmarks
├── results/                 # Experimental results (CSV, JSON)
├── figures/                 # Generated plots and visualizations
├── tests/                   # Unit and integration tests
└── docs/                    # Additional documentation
```

## Quick Start

### Prerequisites

- Python 3.9+
- NumPy, SciPy, NetworkX, Matplotlib
- Optional: Jason framework for BDI baseline

### Installation

```bash
# Clone and install
cd osl_implementation
pip install -r requirements.txt
pip install -e .

# Run all experiments (takes ~30 minutes)
python run_all_experiments.py

# View results
ls results/
ls figures/
```

### Individual Experiments

```bash
# Performance benchmarks
python experiments/performance/rbp_scaling.py
python experiments/performance/mcc_performance.py

# Theory-of-Mind evaluation
python experiments/theory_of_mind/sally_anne.py
python experiments/theory_of_mind/false_belief_suite.py

# Multi-agent coordination
python experiments/multi_agent/coordination_benchmark.py

# Explanation quality
python experiments/explanation/explanation_metrics.py
```

## Core Implementation

### OSL Lattice Structure

The core lattice implementation supports:
- Product lattice construction from observer and situation hierarchies
- Efficient join/meet operations with caching
- Ancestor/descendant cone computation
- Balanced lattice optimization

```python
from src.osl import OSLattice, BeliefBase

# Create lattice
observers = ['camera', 'robot', 'human']  # Ordered by capability
situations = ['morning', 'emergency']     # Ordered by specificity
lattice = OSLattice(observers, situations)

# Manage beliefs
belief_base = BeliefBase(lattice)
belief_base.add_belief('spill_detected', ('camera', 'morning'), 0.9)
```

### Relativized Belief Propagation (RBP)

Efficient belief update algorithm with sub-linear complexity:

```python
# Update belief with automatic propagation
belief_base.rbp_update('spill_detected', ('robot', 'emergency'), 0.8)

# Query beliefs from any perspective
result = belief_base.query('spill_detected', ('human', 'morning'))
```

### Minimal Contradiction Decomposition (MCC)

Automatic contradiction detection and resolution:

```python
# Detect contradictions
contradictions = belief_base.find_contradictions()

# Get minimal contradiction components
mccs = belief_base.minimal_contradiction_decomposition()
```

## Experimental Validation

### Performance Benchmarks

**RBP Scaling Test** (`experiments/performance/rbp_scaling.py`):
- Tests lattice sizes from 10² to 10⁴ elements
- Measures update time vs lattice size
- Confirms O(√n) scaling in balanced lattices
- Compares against linear and quadratic baselines

**MCC Performance** (`experiments/performance/mcc_performance.py`):
- Evaluates contradiction detection speed
- Tests O(|B|log|B|) complexity claims
- Compares with AGM truth maintenance systems

### Theory-of-Mind Evaluation

**Sally-Anne Test** (`experiments/theory_of_mind/sally_anne.py`):
- Implements classic false-belief scenario
- Demonstrates automatic ToM reasoning via lattice operations
- Compares with specialized ToM systems

**False Belief Suite** (`experiments/theory_of_mind/false_belief_suite.py`):
- Comprehensive ToM benchmark including:
  - First-order false beliefs
  - Second-order false beliefs  
  - Unexpected contents tasks
  - Appearance-reality distinctions

### Multi-Agent Coordination

**Coordination Benchmark** (`experiments/multi_agent/coordination_benchmark.py`):
- Mars rover exploration scenario
- 3 agents with different sensor capabilities
- Measures task completion rates and communication overhead
- Compares OSL vs traditional BDI coordination

### Explanation Quality Assessment

**Explanation Metrics** (`experiments/explanation/explanation_metrics.py`):
- Automated evaluation of explanation quality
- Metrics: completeness, conciseness, perspective-appropriateness
- Comparison with LIME, SHAP, and BDI trace explanations

## Baseline Implementations

### BDI Baseline (`baselines/bdi_baseline.py`)
- Simplified BDI agent with single belief base per agent
- Message-passing coordination protocol
- Context switching via belief base replacement

### AGM Truth Maintenance (`baselines/agm_tms.py`)
- Dependency-based truth maintenance system
- AGM-style belief revision with entrenchment
- Quadratic worst-case complexity for contradiction resolution

### Epistemic Planner (`baselines/epistemic_planner.py`)
- Modal logic representation of nested beliefs
- Exponential complexity in belief nesting depth
- Limited to small-scale scenarios

## Result Generation

All experimental results are automatically generated and saved in standardized formats:

- **Performance data**: CSV files with timing measurements
- **Accuracy metrics**: JSON files with correctness scores  
- **Visualizations**: PDF/PNG plots for paper figures
- **Statistical analysis**: Confidence intervals and significance tests

### Key Result Files

- `results/rbp_scaling_results.csv` - RBP performance data
- `results/tom_accuracy_results.json` - Theory-of-Mind scores
- `results/coordination_results.csv` - Multi-agent performance
- `figures/performance_comparison.pdf` - Main performance plot
- `figures/tom_benchmark_results.pdf` - ToM evaluation chart

## Reproducibility

### Deterministic Results
- Fixed random seeds for all experiments
- Deterministic lattice generation algorithms
- Consistent experimental parameters across runs

### Statistical Validation
- Multiple runs (100 iterations) for timing measurements
- Confidence intervals and error bars
- Statistical significance testing where appropriate

### Hardware Requirements
- Minimum: 8GB RAM, 4 CPU cores
- Recommended: 16GB RAM, 8 CPU cores
- Estimated runtime: 30 minutes for all experiments

## Verification and Testing

### Unit Tests (`tests/`)
- Core lattice operations
- Belief management functions
- Algorithm correctness verification
- Edge case handling

### Integration Tests
- End-to-end scenario testing
- Baseline comparison validation
- Result consistency checks

### Run Tests
```bash
python -m pytest tests/ -v
```

## Implementation Notes

### Performance Optimizations
- Memoized lattice operations (join/meet caching)
- Incremental belief propagation
- Efficient ancestor/descendant enumeration
- Batch processing for multiple updates

### Memory Management
- Lazy evaluation of lattice cones
- Garbage collection of unused belief records
- Memory-mapped storage for large datasets

### Extensibility
- Modular architecture for easy extension
- Plugin system for new algorithms
- Configurable lattice structures

## Troubleshooting

### Common Issues

**Memory errors with large lattices**:
```bash
# Reduce lattice size or enable memory optimization
export OSL_MEMORY_OPTIMIZE=1
python experiments/performance/rbp_scaling.py --max_size 1000
```

**Slow baseline comparisons**:
```bash
# Skip expensive baselines for quick testing
python run_all_experiments.py --skip_baselines
```

**Missing dependencies**:
```bash
# Install all optional dependencies
pip install -r requirements.txt
pip install jason-framework  # For BDI baseline
```

### Performance Tuning

For optimal performance on your hardware:

```python
# Adjust cache sizes
OSL_CACHE_SIZE = 10000  # Increase for more memory

# Enable parallel processing
OSL_PARALLEL = True
OSL_NUM_THREADS = 8
```

## Citation

If you use this implementation, please cite:

```bibtex
@inproceedings{anonymous2026osl,
  title={The Observer-Situation Lattice: A Unified Formal Basis for Perspective-Aware Cognition},
  author={Anonymous},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence},
  year={2026}
}
```

## License

This code is provided for research purposes only. See LICENSE file for details.

## Contact

For questions about this implementation, please contact the anonymous authors through the conference review system.

---

**Note for Reviewers**: This implementation is designed to be completely self-contained and reproducible. All claimed results in the paper can be generated by running the provided scripts. The codebase is well-documented and tested to facilitate review and potential future research.

