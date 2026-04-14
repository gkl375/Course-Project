"""Step-by-step heap tree PNG diagrams (requires matplotlib)."""

import math
import os
import textwrap
from typing import Dict, List, Optional, Tuple

from .heapsort import heapify
from .max_heap import MaxHeap

# Export tuning: figures are often placed at ~half an A4 page; use large type + DPI so print stays legible.
_HEAP_TREE_DPI = 300
_HEAP_TREE_FIGSIZE = (15, 9)
_STEP_LABEL_FONTSIZE = 30
_TITLE_FONTSIZE = 24
_TITLE_WRAP_WIDTH = 44
_NODE_VALUE_FONTSIZE = 24
_INDEX_LABEL_FONTSIZE = 20
_ARRAY_FOOTER_FONTSIZE = 21
_ARRAY_WRAP_WIDTH = 64
_EMPTY_HEAP_FONTSIZE = 21
_SCATTER_POINTSIZE = 3200
_NODE_EDGE_WIDTH = 2.4
_BRANCH_LINEWIDTH = 1.65
# Figure coordinates: header stack and plot area (avoid Step / title overlap).
_FIG_STEP_Y = 0.99
_FIG_TITLE_TOP_Y = 0.905
_AX_RECT = (0.055, 0.115, 0.89, 0.695)
_FIG_ARRAY_Y = 0.048
# Tree layout in axes coordinates (extra vertical gap reduces parent i= vs child-node overlap).
_TREE_ROOT_Y = 0.87
_TREE_LEVEL_SPAN = 0.58


def _draw_heap_tree_png(
    arr: List[int],
    step_no: int,
    title: str,
    out_png: str,
    highlight_indices: Optional[set] = None,
    dim_indices: Optional[set] = None,
) -> None:
    """
    Draw array-represented heap as a binary tree diagram.

    highlight_indices: nodes to color (operation in this step)
    dim_indices: nodes to gray-out (e.g., sorted tail in heapsort)
    """
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "matplotlib is required to export diagrams. Install it with: pip install matplotlib"
        ) from e

    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    n = len(arr)
    highlight_indices = highlight_indices or set()
    dim_indices = dim_indices or set()

    fig = plt.figure(figsize=_HEAP_TREE_FIGSIZE)
    ax = fig.add_axes(list(_AX_RECT))
    ax.axis("off")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(0.0, 1.0)

    fig.text(
        0.5,
        _FIG_STEP_Y,
        f"Step {step_no}",
        ha="center",
        va="top",
        fontsize=_STEP_LABEL_FONTSIZE,
        fontweight="bold",
    )
    title_wrapped = "\n".join(textwrap.wrap(title, width=_TITLE_WRAP_WIDTH))
    fig.text(
        0.5,
        _FIG_TITLE_TOP_Y,
        title_wrapped,
        ha="center",
        va="top",
        fontsize=_TITLE_FONTSIZE,
        linespacing=1.35,
    )

    if n == 0:
        ax.text(
            0.5,
            0.45,
            "(empty)",
            ha="center",
            va="center",
            fontsize=_EMPTY_HEAP_FONTSIZE,
        )
        array_text = "array = []"
        fig.text(
            0.5,
            _FIG_ARRAY_Y,
            array_text,
            ha="center",
            va="bottom",
            fontsize=_ARRAY_FOOTER_FONTSIZE,
            family="monospace",
        )
        plt.savefig(out_png, dpi=_HEAP_TREE_DPI)
        plt.close()
        return

    levels = int(math.floor(math.log2(n))) + 1
    positions: Dict[int, Tuple[float, float]] = {}
    denom_level = max(levels - 1, 1)
    for i in range(n):
        level = int(math.floor(math.log2(i + 1)))
        idx_in_level = i - (2**level - 1)
        denom = max(1, 2**level)
        x = (idx_in_level + 0.5) / denom
        y = _TREE_ROOT_Y - level * (_TREE_LEVEL_SPAN / denom_level)
        positions[i] = (x, y)

    for i in range(n):
        l = 2 * i + 1
        r = 2 * i + 2
        x0, y0 = positions[i]
        if l < n:
            x1, y1 = positions[l]
            t1, t2 = 0.08, 0.92
            ax.plot(
                [x0 + (x1 - x0) * t1, x0 + (x1 - x0) * t2],
                [y0 + (y1 - y0) * t1, y0 + (y1 - y0) * t2],
                "-",
                color="#9aa0a6",
                linewidth=_BRANCH_LINEWIDTH,
                zorder=1,
            )
        if r < n:
            x1, y1 = positions[r]
            t1, t2 = 0.08, 0.92
            ax.plot(
                [x0 + (x1 - x0) * t1, x0 + (x1 - x0) * t2],
                [y0 + (y1 - y0) * t1, y0 + (y1 - y0) * t2],
                "-",
                color="#9aa0a6",
                linewidth=_BRANCH_LINEWIDTH,
                zorder=1,
            )

    xs = []
    ys = []
    fcs = []
    ecs = []
    for i in range(n):
        x, y = positions[i]
        xs.append(x)
        ys.append(y)
        if i in dim_indices:
            fcs.append("#e6e6e6")
            ecs.append("#bdbdbd")
        elif i in highlight_indices:
            fcs.append("#ff7f0e")
            ecs.append("#ff7f0e")
        else:
            fcs.append("white")
            ecs.append("#1f77b4")

    ax.scatter(
        xs,
        ys,
        s=_SCATTER_POINTSIZE,
        c=fcs,
        edgecolors=ecs,
        linewidths=_NODE_EDGE_WIDTH,
        zorder=3,
    )

    # Place index labels just under the marker (va=top) so larger type does not sit on the child row.
    idx_anchor_dy = 0.055 + (_INDEX_LABEL_FONTSIZE / 900.0)
    for i in range(n):
        x, y = positions[i]
        value_color = "#111111" if i in dim_indices else ("white" if i in highlight_indices else "#1f77b4")
        ax.text(
            x,
            y,
            str(arr[i]),
            ha="center",
            va="center",
            color=value_color,
            fontsize=_NODE_VALUE_FONTSIZE,
            fontweight="bold",
            zorder=4,
        )
        ax.text(
            x,
            y - idx_anchor_dy,
            f"i={i}",
            ha="center",
            va="top",
            color="#333333",
            fontsize=_INDEX_LABEL_FONTSIZE,
            zorder=4,
        )

    wrapped = textwrap.fill(f"array = {arr}", width=_ARRAY_WRAP_WIDTH)
    fig.text(
        0.5,
        _FIG_ARRAY_Y,
        wrapped,
        ha="center",
        va="bottom",
        fontsize=_ARRAY_FOOTER_FONTSIZE,
        family="monospace",
        linespacing=1.3,
    )

    plt.savefig(out_png, dpi=_HEAP_TREE_DPI)
    plt.close()


def export_step_diagrams(out_dir: str = "diagrams") -> None:
    """
    Export step-by-step diagrams for:
      - MaxHeap insert/extract maintenance (swim-up / sink-down)
      - Heapsort: one frame before build_max_heap, one per sift-down swap during build,
        one frame after build, then sort phase (root–tail swap + heapify per extraction)
    """
    os.makedirs(out_dir, exist_ok=True)

    # MaxHeap frames: insert 1..7 (matches demo.py and maxheap_step_transitions.csv).
    seq = [1, 2, 3, 4, 5, 6, 7]
    h = MaxHeap(trace=False)
    step = 0

    _draw_heap_tree_png(
        h.heap,
        step_no=step,
        title="MaxHeap (start empty)",
        out_png=os.path.join(out_dir, f"maxheap_{step:02d}_start.png"),
        highlight_indices=set(),
        dim_indices=set(),
    )

    for x in seq:
        step += 1
        touched: set[int] = set()

        def recorder(i: int, j: int) -> None:
            touched.add(i)
            touched.add(j)

        h._swap_recorder = recorder  # type: ignore[attr-defined]
        h.insert(x)
        h._swap_recorder = None  # type: ignore[attr-defined]

        highlight = {idx for idx in touched if 0 <= idx < len(h.heap)}
        _draw_heap_tree_png(
            h.heap,
            step_no=step,
            title=f"After insert {x} (swim-up)",
            out_png=os.path.join(out_dir, f"maxheap_{step:02d}_insert_{x}.png"),
            highlight_indices=highlight,
            dim_indices=set(),
        )

    while not h.is_empty():
        step += 1
        touched = set()

        def recorder(i: int, j: int) -> None:
            touched.add(i)
            touched.add(j)

        h._swap_recorder = recorder  # type: ignore[attr-defined]
        m = h.extract_max()
        h._swap_recorder = None  # type: ignore[attr-defined]

        highlight = {idx for idx in touched if 0 <= idx < len(h.heap)}
        _draw_heap_tree_png(
            h.heap,
            step_no=step,
            title=f"After extract_max -> {m} (sink-down)",
            out_png=os.path.join(out_dir, f"maxheap_{step:02d}_extract_{m}.png"),
            highlight_indices=highlight,
            dim_indices=set(),
        )

    # Heapsort frames: same demo array as heapsort_step_transitions.csv.
    arr = [1, 7, 6, 23, 4, 16]
    n = len(arr)
    step = 0
    build_swap_no = 0

    # Step 0 matches CSV row phase=Start.
    _draw_heap_tree_png(
        arr[:],
        step_no=step,
        title="Heapsort — initial array; build_max_heap begins (input not a heap)",
        out_png=os.path.join(out_dir, f"heapsort_{step:02d}_before_build.png"),
        highlight_indices=set(),
        dim_indices=set(),
    )
    step += 1

    def rec_build_swap(i: int, j: int) -> None:
        nonlocal step, build_swap_no
        build_swap_no += 1
        _draw_heap_tree_png(
            arr[:],
            step_no=step,
            title=(
                f"build_max_heap — after swap {build_swap_no} "
                f"(indices {i} ↔ {j})"
            ),
            out_png=os.path.join(
                out_dir, f"heapsort_{step:02d}_build_swap_{build_swap_no:02d}.png"
            ),
            highlight_indices={i, j},
            dim_indices=set(),
        )
        step += 1

    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i, trace=False, swap_recorder=rec_build_swap)

    _draw_heap_tree_png(
        arr[:],
        step_no=step,
        title="Heapsort — after build_max_heap (max-heap; start sort phase)",
        out_png=os.path.join(out_dir, f"heapsort_{step:02d}_after_build.png"),
        highlight_indices=set(),
        dim_indices=set(),
    )

    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        step += 1
        dim = set(range(end, n))
        _draw_heap_tree_png(
            arr[:],
            step_no=step,
            title=f"Swap root <-> end={end}",
            out_png=os.path.join(out_dir, f"heapsort_{step:02d}_swap_end_{end}.png"),
            highlight_indices={0, end},
            dim_indices=dim,
        )

        touched = set()

        def rec_heapify(i: int, j: int) -> None:
            touched.add(i)
            touched.add(j)

        heapify(arr, end, 0, trace=False, swap_recorder=rec_heapify)
        step += 1
        dim = set(range(end, n))
        _draw_heap_tree_png(
            arr[:],
            step_no=step,
            title=f"Heapify reduced heap size={end}",
            out_png=os.path.join(out_dir, f"heapsort_{step:02d}_heapify_end_{end}.png"),
            highlight_indices={idx for idx in touched if 0 <= idx < end},
            dim_indices=dim,
        )
