"""
Console demos: MaxHeap maintenance, small applications, and heapsort vs ``sorted()``.

Intended for lecturers/students to see behavior and to sanity-check the implementation.
"""

from typing import List

from .heapsort import heap_sort
from .max_heap import MaxHeap


def correctness_demo():
    """Print scenarios; assert heap shape and that ``heap_sort`` matches ``sorted()``."""

    # Only internal nodes (indices 0 .. n//2-1) can have children to check.
    def verify_heap_property(heap_arr):
        for i in range(len(heap_arr) // 2):
            l = 2 * i + 1
            r = 2 * i + 2
            if l < len(heap_arr) and heap_arr[i] < heap_arr[l]:
                return False
            if r < len(heap_arr) and heap_arr[i] < heap_arr[r]:
                return False
        return True

    print("== Heap: MaxHeap examples (insert, peek, extract_max) ==")

    print("\n[heap] Maintenance (diagrams + maxheap_step_transitions.csv)")
    print("  insert keys 1..7 in order (heap array = level-order storage).")
    insert_seq = [1, 2, 3, 4, 5, 6, 7]
    h = MaxHeap(trace=False)
    for x in insert_seq:
        h.insert(x)
        # Catch heap-order regressions immediately during insert trace.
        assert verify_heap_property(h.heap)
        print(f"  after insert {x}: heap array = {h.heap}")
    print(f"peek: max key = {h.peek()}")
    while not h.is_empty():
        m = h.extract_max()
        print(f"  extract_max -> removed {m}; heap after = {h.heap}")

    queue_jobs = [
        (25, "P1"),
        (90, "P2"),
        (40, "P3"),
        (15, "P4"),
    ]
    print("\n[heap] Priority queue (higher number = more urgent)")
    prios = [pr for pr, _ in queue_jobs]
    print(f"  arrival order: P1, P2, P3, P4  |  priorities (same order): {prios}")
    for i, (pr, pid) in enumerate(queue_jobs, start=1):
        print(f"  enqueue #{i}: {pid}  priority {pr}")
    h = MaxHeap(trace=False)
    for pr, _ in queue_jobs:
        h.insert(pr)
        # Priority queue behavior depends on max-heap invariant.
        assert verify_heap_property(h.heap)
    pr_to_pid = {pr: pid for pr, pid in queue_jobs}
    pk = h.peek()
    print(f"peek: priority {pk}  ({pr_to_pid[pk]})")
    processed: List[int] = []
    while not h.is_empty():
        processed.append(h.extract_max())
    # Ground-truth check against Python sort in descending priority.
    expected = sorted([p for p, _ in queue_jobs], reverse=True)
    served = ", ".join(f"{p} ({pr_to_pid[p]})" for p in processed)
    print(f"  extract_max by priority: {served} | ok={processed == expected}")

    data = [23, 15, 42, 38, 19, 27, 31, 11]
    k = 3
    print("\n[heap] Top-K largest (extract K times from max-heap)")
    print(f"  values: {data}")
    h = MaxHeap(trace=False)
    for x in data:
        h.insert(x)
        assert verify_heap_property(h.heap)
    # Top-K by repeated extract_max from the built heap.
    top_k = [h.extract_max() for _ in range(k)]
    expected_top_k = sorted(data, reverse=True)[:k]
    print(f"  top {k} largest: {top_k} | ok={top_k == expected_top_k}")

    print("\n== Heapsort examples (heap_sort + correctness) ==")

    samples = [
        ("trace demo (swap steps in tables/heapsort_step_transitions.csv)", [1, 7, 6, 23, 4, 16]),
        ("random", [64, 34, 25, 12, 22, 11, 90]),
        ("with duplicates", [3, 1, 4, 1, 5, 9, 2, 6]),
        ("already sorted", [1, 2, 3, 4, 5, 6, 7]),
        ("reverse sorted", [7, 6, 5, 4, 3, 2, 1]),
        ("negatives + duplicates", [0, -1, 5, -10, 5, 3, 0]),
        ("all identical", [42, 42, 42, 42, 42]),
        ("empty", []),
        ("single", [99]),
    ]

    for name, a in samples:
        print(f"\n[heapsort] case='{name}'")
        print(f"[heapsort] input : {a}")
        b = a[:]
        heap_sort(b, trace=False)
        # Compare against trusted reference implementation.
        ok = (b == sorted(a))
        print(f"[heapsort] output: {b}")
        print(f"[heapsort] sorted_ok={ok}")
