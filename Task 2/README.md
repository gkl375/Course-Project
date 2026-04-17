# Heap & Heapsort — User Guide

Self-study project for a **binary max-heap** (array-based) and **heapsort**.

## Introduction video

https://github.com/user-attachments/assets/e7a10fbf-237f-454f-8c71-9c09181f806f

---

## Quick start

1. **Clone or download** this repository.
2. Open a terminal in the **project root** (the folder that contains `heap_heapsort_project.py` and the `heap_heapsort/` package).
3. Run:

```bash
python heap_heapsort_project.py
```

**Equivalent:**

```bash
python -m heap_heapsort
```

> **Important:** Commands must be run from the **repository root**. If Python cannot find `heap_heapsort`, you are probably in the wrong directory.

---

## Requirements

| Component | Notes |
|-----------|--------|
| **Python** | **3.9+** recommended (stdlib suffices for algorithms; modern type hints). |
| **matplotlib** | **Optional.** Needed for step PNG diagrams under `diagrams/` and timing **PNG** plots under `results/`. Without it, console demos, CSV tables, and benchmark **CSV** still run. |

Install optional dependencies (diagrams and benchmark plots):

```bash
pip install -r requirements.txt
```

`matplotlib` is the only third-party package needed for the default pipeline’s PNG outputs; the rest of the run works without it.

---

## What the default run does

Running `heap_heapsort_project.py` or `python -m heap_heapsort` executes `heap_heapsort.run.main()` in order:

| Step | Action | Output |
|------|--------|--------|
| 1 | **Correctness demo** (`correctness_demo`) | Console: MaxHeap insert/extract trace `1..7`, priority-queue example, top-K, heapsort cases with `sorted_ok=True`. |
| 2 | **Step diagrams** | If matplotlib is available: PNGs under **`diagrams/`** (MaxHeap trace, heapsort trace for `[1, 7, 6, 23, 4, 16]`). |
| 3 | **CSV tables** | **`tables/`**: e.g. `heap_index_mapping.csv`, `heapsort_step_transitions.csv`, `maxheap_step_transitions.csv`. |
| 4 | **Benchmarks** | **`results/`**: `time_complexity_bench_multi_n.csv`; with matplotlib, per-scenario fit plots and summary PNGs. |

If matplotlib is missing, a short message is printed and diagrams/plots are skipped; the rest completes.

---

## Project layout

| Path | Role |
|------|------|
| `heap_heapsort_project.py` | **Main entry** — runs the full pipeline. |
| `heap_heapsort/` | **Package** — library, demos, diagrams, tables, benchmarks. |
| `heap_heapsort/max_heap.py` | `MaxHeap` (insert, peek, extract_max, swim-up / sink-down). |
| `heap_heapsort/heapsort.py` | `heapify`, `build_max_heap`, `heap_sort`. |
| `heap_heapsort/demo.py` | `correctness_demo()` — console examples and checks. |
| `heap_heapsort/run.py` | Wires `main()`: demo → diagrams → tables → benchmark. |
| `heap_heapsort/diagrams.py` | Exports step PNGs (requires matplotlib). |
| `heap_heapsort/tables.py` | Writes CSVs under `tables/`. |
| `heap_heapsort/benchmark.py` | Multi-size timing + CSV/PNG under `results/`. |
| `heap_heapsort_flowchart.md` | Mermaid flowcharts (renders on GitHub). |

---

## Using the library in your own script

Run from the **project root** so `heap_heapsort` resolves as a package:

```python
from heap_heapsort import MaxHeap, heap_sort

h = MaxHeap()
h.insert(5)
h.insert(9)
print(h.extract_max())  # 9

a = [3, 1, 4]
heap_sort(a)
print(a)  # [1, 3, 4]
```

---

## Reproducibility

- Benchmark sizes and random seeds are fixed inside `heap_heapsort/benchmark.py` (e.g. `seed = 2026`, `n = 2**k` for `k` in `10..16`).
- Absolute timings and `R²` values depend on your machine; trends should match **Θ(n log n)** for heapsort.

---

## Further reading

- **Algorithm flow:** [`heap_heapsort_flowchart.md`](heap_heapsort_flowchart.md) (Mermaid on GitHub).
