"""CSV tables: heap index mapping and step transitions."""

import csv
import os
from typing import Dict, List, Tuple

from .heapsort import build_max_heap
from .max_heap import MaxHeap


def _maxheap_array_after_inserts(insert_sequence: List[int]) -> List[int]:
    """Heap array snapshot after inserting all values (same order as MaxHeap demo)."""
    h = MaxHeap(trace=False)
    for x in insert_sequence:
        h.insert(x)
    return h.heap[:]


def _heap_link_str(idx: int) -> str:
    """Print index for CSV: missing parent/child uses the word none (not -1)."""
    if idx < 0:
        return "none"
    return str(idx)


def _local_max_heap_ok_at_node(i: int, values: List[int], n: int) -> bool:
    """True iff values[i] is >= each existing child (max-heap rule at this node)."""
    v = values[i]
    li = 2 * i + 1
    ri = 2 * i + 2
    if li < n and v < values[li]:
        return False
    if ri < n and v < values[ri]:
        return False
    return True


def heap_index_mapping_rows(
    n: int,
    value_at_index: List[int],
    demo_context: str,
) -> List[Dict]:
    """
    Array heap: parent(i)=(i-1)//2, left=2i+1, right=2i+2.
    CSV uses the word none for a missing link (root has no parent; leaves have no children).
    """
    if len(value_at_index) != n:
        raise ValueError("value_at_index length must equal n")
    rows: List[Dict] = []
    full_arr = str(value_at_index[:])
    for i in range(n):
        parent_raw = (i - 1) // 2 if i > 0 else -1
        li = 2 * i + 1
        ri = 2 * i + 2
        left_raw = li if li < n else -1
        right_raw = ri if ri < n else -1
        local_ok = _local_max_heap_ok_at_node(i, value_at_index, n)
        rows.append(
            {
                "demo_context": demo_context,
                "full_array_demo": full_arr,
                "index": i,
                "value_at_index": value_at_index[i],
                "parent_index": _heap_link_str(parent_raw),
                "left_child_index": _heap_link_str(left_raw),
                "right_child_index": _heap_link_str(right_raw),
                "local_max_heap_ok": "yes" if local_ok else "no",
            }
        )
    return rows


def heapsort_step_transition_rows(initial: List[int]) -> List[Dict]:
    """
    Record every swap during build_max_heap and sort phase (same logic as heapify / heap_sort).
    Phase and operation use readable English (see heap_heapsort.heapsort).
    """
    arr = initial[:]
    n = len(arr)
    rows: List[Dict] = []
    step = 0

    ph_start = "Start"
    ph_build = "build_max_heap"
    ph_sort = "heap_sort"
    ph_done = "Done"

    def push(
        phase: str,
        operation: str,
        heap_size: int,
        swap_index_1: str,
        swap_index_2: str,
        swap_meaning: str,
    ) -> None:
        nonlocal step
        rows.append(
            {
                "step": step,
                "phase": phase,
                "operation": operation,
                "heap_size": heap_size,
                "swap_index_1": swap_index_1,
                "swap_index_2": swap_index_2,
                "swap_meaning": swap_meaning,
                "array": str(arr[:]),
            }
        )
        step += 1

    push(
        ph_start,
        "Initial array before build_max_heap; build_max_heap begins",
        n,
        "",
        "",
        "No swap in this row",
    )

    # Recursive sift-down (same comparisons as ``heapsort.heapify``); logs each swap.
    def heapify_rec(heap_size: int, i: int, phase: str, op_swap: str) -> None:
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        if left < heap_size and arr[left] > arr[largest]:
            largest = left
        if right < heap_size and arr[right] > arr[largest]:
            largest = right
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            push(
                phase,
                op_swap,
                heap_size,
                str(i),
                str(largest),
                "Heapify swap: exchange subtree root index with larger child index",
            )
            heapify_rec(heap_size, largest, phase, op_swap)

    op_sift = "Sift-down during heapify: swap parent with larger child until heap property holds"
    for i in range(n // 2 - 1, -1, -1):
        heapify_rec(n, i, ph_build, op_sift)

    push(
        ph_build,
        "Build max heap finished; the whole array is a max-heap",
        n,
        "",
        "",
        "No swap in this row",
    )

    op_root_end = "Swap root with last index of current heap to place largest value at end"
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        push(
            ph_sort,
            op_root_end,
            end,
            "0",
            str(end),
            "Sort phase swap: exchange root with last index of current heap (move max to sorted tail)",
        )
        heapify_rec(end, 0, ph_sort, op_sift)

    push(
        ph_done,
        "Heap sort finished; array is sorted ascending",
        n,
        "",
        "",
        "No swap in this row",
    )
    return rows


def maxheap_step_transition_rows(insert_sequence: List[int]) -> List[Dict]:
    """
    One row per MaxHeap diagram frame (same cadence as export_step_diagrams).
    swap_index_1 / swap_index_2 = first parent-child swap in that step (i != j).
    swap_meaning lists every swap pair in order (i != j only).
    """
    rows: List[Dict] = []
    step_no = 0
    h = MaxHeap(trace=False)

    def append_row(
        phase: str,
        operation: str,
        heap_snapshot: List[int],
        swap_pairs: List[Tuple[int, int]],
    ) -> None:
        nonlocal step_no
        if swap_pairs:
            s1, s2 = str(swap_pairs[0][0]), str(swap_pairs[0][1])
            all_swaps = ", ".join(f"{a} <-> {b}" for a, b in swap_pairs)
            sm = f"Swaps in order: {all_swaps}"
        else:
            s1, s2 = "", ""
            sm = "No parent-child swap in this step"

        rows.append(
            {
                "step": step_no,
                "phase": phase,
                "operation": operation,
                "heap_size": len(heap_snapshot),
                "swap_index_1": s1,
                "swap_index_2": s2,
                "swap_meaning": sm,
                "array": str(heap_snapshot[:]),
            }
        )
        step_no += 1

    append_row(
        "Start",
        f"MaxHeap (start empty); diagrams/maxheap_{step_no:02d}_start.png",
        [],
        [],
    )

    for x in insert_sequence:
        swap_pairs: List[Tuple[int, int]] = []

        def rec_ins(i: int, j: int) -> None:
            if i != j:
                swap_pairs.append((i, j))

        h._swap_recorder = rec_ins  # type: ignore[attr-defined]
        h.insert(x)
        h._swap_recorder = None  # type: ignore[attr-defined]
        sn = step_no
        append_row(
            "MaxHeap.insert",
            f"After insert {x} (swim-up); diagrams/maxheap_{sn:02d}_insert_{x}.png",
            h.heap[:],
            swap_pairs,
        )

    while not h.is_empty():
        swap_pairs = []

        def rec_ext(i: int, j: int) -> None:
            if i != j:
                swap_pairs.append((i, j))

        h._swap_recorder = rec_ext  # type: ignore[attr-defined]
        m = h.extract_max()
        h._swap_recorder = None  # type: ignore[attr-defined]
        sn = step_no
        append_row(
            "MaxHeap.extract_max",
            f"After extract_max -> {m} (sink-down); diagrams/maxheap_{sn:02d}_extract_{m}.png",
            h.heap[:],
            swap_pairs,
        )

    return rows


def _write_csv(path: str, fieldnames: List[str], rows: List[Dict]) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def export_tables(out_dir: str = "tables") -> None:
    """
    Write CSV tables for reports:
      - heap_index_mapping.csv          tree layout after operations (no raw initial input)
      - heapsort_step_transitions.csv   swap-level trace with swap_index_1/2 and swap_meaning
      - maxheap_step_transitions.csv    one row per MaxHeap diagram step (same as export_step_diagrams)
    """
    heapsort_demo = [1, 7, 6, 23, 4, 16]
    maxheap_ins = [1, 2, 3, 4, 5, 6, 7]
    n_hs = len(heapsort_demo)
    n_mh = len(maxheap_ins)
    maxheap_filled = _maxheap_array_after_inserts(maxheap_ins)

    heapsort_after_build = heapsort_demo[:]
    build_max_heap(heapsort_after_build, trace=False)

    idx_path = os.path.join(out_dir, "heap_index_mapping.csv")
    idx_rows = heap_index_mapping_rows(
        n_hs,
        heapsort_after_build,
        "Heapsort: after build_max_heap",
    ) + heap_index_mapping_rows(
        n_mh,
        maxheap_filled,
        "MaxHeap: after inserting 1 through 7",
    )
    _write_csv(
        idx_path,
        [
            "demo_context",
            "full_array_demo",
            "index",
            "value_at_index",
            "parent_index",
            "left_child_index",
            "right_child_index",
            "local_max_heap_ok",
        ],
        idx_rows,
    )

    hs_path = os.path.join(out_dir, "heapsort_step_transitions.csv")
    _write_csv(
        hs_path,
        [
            "step",
            "phase",
            "operation",
            "heap_size",
            "swap_index_1",
            "swap_index_2",
            "swap_meaning",
            "array",
        ],
        heapsort_step_transition_rows(heapsort_demo),
    )

    mh_path = os.path.join(out_dir, "maxheap_step_transitions.csv")
    _write_csv(
        mh_path,
        [
            "step",
            "phase",
            "operation",
            "heap_size",
            "swap_index_1",
            "swap_index_2",
            "swap_meaning",
            "array",
        ],
        maxheap_step_transition_rows(maxheap_ins),
    )

    print(f"Saved tables to: {out_dir}/")
    print(f"  - {idx_path}")
    print(f"  - {hs_path}")
    print(f"  - {mh_path}")
