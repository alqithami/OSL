# OSL — Observer–Situation Lattice

This repository contains the reference implementation and experimental artifacts for:

**Saad Alqithami. 2026. _The Observer–Situation Lattice: A Unified Formal Basis for Perspective-Aware Cognition_.**  
In: *Proceedings of the 25th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2026)*, Paphos, Cyprus (May 25–29, 2026).  
DOI: **10.65109/CHZG9392**

[![Watch the video](https://github.com/user-attachments/assets/2a28c96c-3f71-4feb-86ae-28a012a596ea)](https://www.youtube.com/watch?v=i7lw2pWrPQA)

---

## What is OSL?

The **Observer–Situation Lattice (OSL)** is a finite product-lattice representation that unifies:

- **Perspective-aware belief management** (different observers can hold different, even contradictory beliefs).
- **Efficient belief propagation** across related perspectives via **RBP** (Refined Belief Propagation).
- **Global consistency repair** via **MCC** (Maximal Consistent Cuts) when contradictions arise.

The implementation provides:

- A concrete OSL lattice and belief base (`src/osl/`).
- RBP + MCC reasoning algorithms.
- Baselines used in the paper (**ATMS**, **DTMS**, **MEPK**) for the runtime/memory comparison.
- Reproducibility scripts for **Table 1–3** and **Figure 3**.

---

## Repository layout

- `src/osl/` — OSL core library (lattice, belief base, algorithms, baselines, CLI)
- `experiments/run.py` — main experiment runner (Tables 1–2 + plots)
- `experiments/tom_suite.py` — Theory-of-Mind scenario suite (Table 3)
- `results_full/` — precomputed outputs matching the paper tables/figures
- `tests/` — unit tests (247 tests run by default; stress tests are optional)
- `Dockerfile` — cross-platform container for tests + quick experiment run
- `.github/workflows/ci.yml` — GitHub Actions workflow (Ubuntu 22.04)

---

## Installation

### Option A — run from source (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -U pip
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

### Option B — minimal runtime install

```bash
pip install -r requirements.txt
```

---

## Reproducing the paper results

### Full suite (Tables 1–3)

```bash
python run_full_experiments.py --output-dir results_full
```

This will generate:

- **Table 1 / Figure 3**: `results_full/baseline_comparison.pdf` and JSON fields under `baseline_comparison`
- **Table 2**:
  - scalability: `results_full/scalability_analysis.pdf` and JSON fields under `scalability`
  - ablation: `results_full/ablation_study.pdf` and JSON fields under `ablation_study`
- **Table 3**: `results_full/tom_suite_results.json`

> Notes on numerical reproducibility  
> Exact runtimes/memory depend on hardware and OS. The paper reports results on a 12‑core ARM laptop (32GB RAM).  
> The **`results_full/`** directory included in this repository contains the numbers used in the paper.

### Quick suite (CI-friendly)

```bash
python run_full_experiments.py --quick --output-dir results_quick
```

This uses reduced trials and smaller problem sizes to finish quickly while still exercising the full pipeline.

---

## Running individual experiments

You can run experiments directly:

```bash
python experiments/run.py --help
```

Examples:

```bash
# Baselines only (Table 1 / Figure 3)
python experiments/run.py --experiment baseline --output-dir results_baseline

# Scalability only (Table 2)
python experiments/run.py --experiment scalability --output-dir results_scalability

# Ablation only (Table 2)
python experiments/run.py --experiment ablation --output-dir results_ablation
```

Theory-of-Mind suite (Table 3):

```bash
python experiments/tom_suite.py --print-table --output results_full/tom_suite_results.json
```

---

## Tests

Run the default unit tests (247 tests; excludes stress tests):

```bash
python run_tests.py
```

With coverage:

```bash
python run_tests.py --coverage
```

Stress tests (large lattices / large belief insertions):

```bash
python run_tests.py --stress
```

---

## Docker

Build:

```bash
docker build -t osl .
```

Run the default container command (tests + quick experiments):

```bash
docker run --rm -it osl
```

To persist outputs to your host machine:

```bash
docker run --rm -it -v "$PWD/results_docker:/app/results_docker" osl
```

---

## CLI wrapper

If installed editable (`pip install -e .`), you can use:

```bash
osl experiments --quick --output-dir results_quick
osl tom --print-table --output results_full/tom_suite_results.json
osl test --coverage
```

---

## Citation

If you use this code, please cite:

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

---

## License

- **Code**: MIT (see `LICENSE`)
- **Paper text**: Creative Commons Attribution 4.0 (CC BY 4.0), as stated in the AAMAS proceedings.
