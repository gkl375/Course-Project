"""
Default pipeline: console demo, optional PNG diagrams, CSV tables, benchmarks.

Mermaid flowcharts live in ``heap_heapsort_flowchart.md`` (not generated here).

Run via ``python heap_heapsort_project.py`` or ``python -m heap_heapsort`` from the repo root.
"""

import os

from .benchmark import benchmark_comparable_examples
from .demo import correctness_demo
from .diagrams import export_step_diagrams
from .tables import export_tables


def main():
    # 1) Printed examples and assertions (no matplotlib required).
    correctness_demo()

    try:
        import matplotlib.pyplot as _plt  # noqa: F401
        export_step_diagrams("diagrams")
        print("\nSaved step diagrams to: diagrams/")
    except Exception:
        print("\nNote: step diagrams were not exported because matplotlib is not available.")

    print("\n== Tables (step transitions + index mapping) ==")
    export_tables("tables")

    out_dir = "results"
    os.makedirs(out_dir, exist_ok=True)

    print("\n== Time complexity benchmark + fitting ==")
    # 2) Timing CSV; PNG fits if matplotlib is installed.
    benchmark_comparable_examples(out_dir)
