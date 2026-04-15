# Observer-Situation Lattice (OSL)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/arXiv-2603.01407-b31b1b.svg)](https://arxiv.org/abs/2603.01407)

[![Banner](https://github.com/user-attachments/assets/770f1aba-18da-4a8d-8e87-fd2d80e5578e)](https://www.youtube.com/watch?v=i7lw2pWrPQA)

**OSL** is a Python reference implementation of the **Observer-Situation Lattice**, a formal mathematical structure for unifying perspective-aware cognition in multi-agent systems. This repository contains the full source code, experimental artifacts, and reproducibility scripts for the AAMAS 2026 paper:

> **The Observer–Situation Lattice: A Unified Formal Basis for Perspective-Aware Cognition**  
> Saad Alqithami  
> *Proceedings of the 25th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2026)*  
> DOI: `10.65109/CHZG9392`

[![Watch the video](https://img.youtube.com/vi/i7lw2pWrPQA/maxresdefault.jpg)](https://www.youtube.com/watch?v=i7lw2pWrPQA)

---

## Core Concept

In complex multi-agent environments, autonomous agents often develop conflicting beliefs due to their unique perspectives. The Observer-Situation Lattice (OSL) provides a unified mathematical framework to manage these divergent viewpoints. It enables agents to represent, propagate, and reconcile beliefs, leading to globally consistent and coordinated behavior.

![Graphical Abstract](https://github.com/user-attachments/assets/0cea6eeb-3f8d-4ca1-9bfc-d8f15435234d)

Key capabilities of the OSL framework include:

*   **Perspective-Aware Belief Management**: Allows different agents (observers) to maintain distinct and even contradictory beliefs based on their unique situations.
*   **Efficient Belief Propagation (RBP)**: A Refined Belief Propagation algorithm that efficiently shares and updates beliefs across the lattice structure.
*   **Global Consistency Repair (MCC)**: A Maximal Consistent Cuts algorithm that identifies and resolves contradictions to restore global consistency.

---

## Repository Structure

This repository is organized to support full reproducibility of the paper's findings.

| Path | Description |
|---|---|
| `src/osl/` | Core OSL library, including the lattice, belief base, RBP/MCC algorithms, and baselines. |
| `experiments/` | Scripts for running the main experiments (Tables 1-2) and the Theory-of-Mind suite (Table 3). |
| `results_full/` | Pre-computed raw data and plots that match the figures and tables in the published paper. |
| `tests/` | A suite of 247 unit tests and optional stress tests for verifying correctness and performance. |
| `Dockerfile` | A containerized environment for cross-platform execution of tests and experiments. |
| `run_*.py` | Top-level scripts for easily running tests and experiments. |

---

## Getting Started

### Installation

You can set up the project by running from source (recommended for development and experimentation) or by installing the minimal runtime dependencies.

**Option A: Run from Source (Recommended)**

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

# Install dependencies
pip install -U pip
pip install -r requirements.txt -r requirements-dev.txt

# Install the OSL package in editable mode
pip install -e .
```

**Option B: Minimal Runtime Install**

```bash
pip install -r requirements.txt
```

### Docker

For a fully containerized and reproducible environment, you can use the provided Dockerfile.

```bash
# Build the Docker image
docker build -t osl .

# Run the default container command (tests + quick experiments)
docker run --rm -it osl

# To persist results to your local machine, mount a volume
docker run --rm -it -v "$PWD/results_docker:/app/results_docker" osl
```

---

## Reproducing Paper Results

This repository provides scripts to reproduce all tables and figures from the paper.

### Full Experiment Suite

To run the complete set of experiments and generate all results (Tables 1–3 and Figure 3), execute:

```bash
python run_full_experiments.py --output-dir results_full
```

> **Note on Reproducibility**: Exact runtimes and memory usage may vary depending on your hardware and OS. The `results_full/` directory contains the precise data generated on a 12-core ARM laptop with 32GB RAM, as reported in the paper.

### Quick Suite (CI-Friendly)

For a faster, CI-friendly run that exercises the full pipeline with reduced trials and problem sizes, use the `--quick` flag:

```bash
python run_full_experiments.py --quick --output-dir results_quick
```

### Individual Experiments

You can also run specific experiments individually.

```bash
# Baseline comparison (Table 1 / Figure 3)
python experiments/run.py --experiment baseline --output-dir results_baseline

# Scalability analysis (Table 2)
python experiments/run.py --experiment scalability --output-dir results_scalability

# Theory-of-Mind suite (Table 3)
python experiments/tom_suite.py --print-table --output results_full/tom_suite_results.json
```

---

## Command-Line Interface

When installed in editable mode, the `osl` CLI wrapper provides convenient shortcuts for common tasks:

```bash
# Run the quick experiment suite
osl experiments --quick --output-dir results_quick

# Run the Theory-of-Mind suite
osl tom --print-table

# Run tests with coverage
osl test --coverage
```

---

## Citation

If you use this work, please cite the following paper:

```bibtex
@inproceedings{alqithami2026osl,
  title     = {The Observer--Situation Lattice: A Unified Formal Basis for Perspective-Aware Cognition},
  author    = {Alqithami, Saad},
  booktitle = {Proceedings of the 25th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2026)},
  year      = {2026},
  address   = {Paphos, Cyprus},
  month     = {May},
  doi       = {10.65109/CHZG9392}
}
```

## License

*   **Code**: [MIT License](LICENSE)
*   **Paper**: Creative Commons Attribution 4.0 (CC BY 4.0)
