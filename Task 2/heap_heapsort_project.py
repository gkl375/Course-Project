"""
Heap + Heapsort project entry point.

Code lives in the ``heap_heapsort`` package:
  - ``max_heap`` / ``heapsort`` — core structures and algorithms
  - ``demo`` — console correctness examples
  - ``diagrams`` — step PNGs (matplotlib); Mermaid flowcharts in ``heap_heapsort_flowchart.md``
  - ``tables`` — CSV tables under ``tables/``
  - ``benchmark`` — multi-n timing + fits under ``results/``

Run from this directory:

  python heap_heapsort_project.py

Or:

  python -m heap_heapsort
"""

from heap_heapsort.run import main

if __name__ == "__main__":
    main()
