"""Course package: MaxHeap, heapsort, demos, diagram/table export, and benchmarks."""

from .benchmark import benchmark_comparable_examples
from .demo import correctness_demo
from .diagrams import export_step_diagrams
from .tables import export_tables
from .heapsort import build_max_heap, heap_sort, heapify
from .max_heap import MaxHeap
from .run import main

__all__ = [
    "MaxHeap",
    "heapify",
    "build_max_heap",
    "heap_sort",
    "correctness_demo",
    "export_step_diagrams",
    "export_tables",
    "benchmark_comparable_examples",
    "main",
]
