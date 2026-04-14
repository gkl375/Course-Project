"""
Empirical timing: build_heap, heapsort, and full MaxHeap insert+extract workloads.

For each (n, scenario) we take the **median** of several wall-clock runs, then fit
time vs n (build) or vs n*log2(n) (sort / PQ-style work) and optionally plot.
"""

import csv
import math
import os
import random
import time
from typing import Callable, Dict, List, Tuple

from .heapsort import build_max_heap, heap_sort
from .max_heap import MaxHeap


def median(values):
    """Median; for even length, average the two middle values."""
    values = sorted(values)
    m = len(values) // 2
    if len(values) % 2 == 1:
        return values[m]
    return 0.5 * (values[m - 1] + values[m])


def run_time_trials(work_fn, trials):
    """Return list of elapsed seconds for ``trials`` runs of ``work_fn``."""
    times = []
    for _ in range(trials):
        # perf_counter provides high-resolution wall-clock timing.
        start = time.perf_counter()
        work_fn()
        end = time.perf_counter()
        times.append(end - start)
    return times


def _linear_fit(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """Fit y ~= a*x + b using least squares. Returns (a, b, r2)."""
    if len(x) != len(y) or len(x) < 2:
        return float("nan"), float("nan"), float("nan")

    x_bar = sum(x) / len(x)
    y_bar = sum(y) / len(y)
    sxx = sum((xi - x_bar) ** 2 for xi in x)
    if sxx == 0:
        return float("nan"), float("nan"), float("nan")

    sxy = sum((xi - x_bar) * (yi - y_bar) for xi, yi in zip(x, y))
    a = sxy / sxx
    b = y_bar - a * x_bar

    y_hat = [a * xi + b for xi in x]
    ss_res = sum((yi - yhi) ** 2 for yi, yhi in zip(y, y_hat))
    ss_tot = sum((yi - y_bar) ** 2 for yi in y)
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0 else float("nan")
    return a, b, r2


def _scenario_arrays(n: int, seed: int) -> Dict[str, List[int]]:
    rng = random.Random(seed)
    # Base sample reused to derive multiple input-shape scenarios.
    base_random = [rng.randint(0, 10**9) for _ in range(n)]

    nearly = sorted(base_random)
    swaps = max(1, n // 100)
    for _ in range(swaps):
        i = rng.randrange(n)
        j = rng.randrange(n)
        nearly[i], nearly[j] = nearly[j], nearly[i]

    few_unique = [rng.randrange(10) for _ in range(n)]

    return {
        "random": base_random,
        "sorted": sorted(base_random),
        "reversed": sorted(base_random, reverse=True),
        "nearly_sorted": nearly,
        "few_unique": few_unique,
    }


def _median_seconds(fn: Callable[[], None], trials: int) -> float:
    """Median runtime of ``fn`` over ``trials`` trials."""
    times = run_time_trials(fn, trials)
    return median(times)


def benchmark_comparable_examples(out_dir: str = "results") -> List[Dict]:
    """
    Comparable performance examples:
      - MaxHeap: insert n + extract n under different input distributions
      - Heapsort: sort under different input distributions
    """
    os.makedirs(out_dir, exist_ok=True)

    trials = 3
    seed = 2026
    n_exps = list(range(10, 17))
    ns = [2**k for k in n_exps]

    print("\n== Comparable performance examples (multi-n, time complexity fit per input distribution) ==")
    print(f"n=2^{n_exps[0]}..2^{n_exps[-1]}, trials={trials} (median)")

    rows: List[Dict] = []

    for n in ns:
        scenarios = _scenario_arrays(n, seed + n)

        # --- build_max_heap only (expect Theta(n)) ---
        for scen_name, scen_arr in scenarios.items():
            def work():
                a = scen_arr[:]
                build_max_heap(a, trace=False)

            med = _median_seconds(work, trials)
            # Fit column uses x = n for linear regression in n.
            fit_x = float(n)
            rows.append(
                {
                    "algorithm": "build_heap",
                    "scenario": scen_name,
                    "n": n,
                    "trials": trials,
                    "median_time_s": med,
                    "fit_x": fit_x,
                }
            )

        # --- full heapsort (expect Theta(n log n)) ---
        for scen_name, scen_arr in scenarios.items():
            def work():
                a = scen_arr[:]
                heap_sort(a, trace=False)

            med = _median_seconds(work, trials)
            # Fit uses x = n*log2(n).
            fit_x = n * math.log2(n) if n > 1 else 1.0
            rows.append(
                {
                    "algorithm": "heapsort",
                    "scenario": scen_name,
                    "n": n,
                    "trials": trials,
                    "median_time_s": med,
                    "fit_x": fit_x,
                }
            )

        # --- n inserts + n extract_max (PQ-style; expect Theta(n log n)) ---
        for scen_name, scen_arr in scenarios.items():
            def work():
                h = MaxHeap(trace=False)
                for x in scen_arr:
                    h.insert(x)
                while not h.is_empty():
                    h.extract_max()

            med = _median_seconds(work, trials)
            # Same x = n*log2(n) as heapsort for regression.
            fit_x = n * math.log2(n) if n > 1 else 1.0
            rows.append(
                {
                    "algorithm": "maxheap_insert_extract",
                    "scenario": scen_name,
                    "n": n,
                    "trials": trials,
                    "median_time_s": med,
                    "fit_x": fit_x,
                }
            )

    csv_path = os.path.join(out_dir, "time_complexity_bench_multi_n.csv")
    os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["algorithm", "scenario", "n", "trials", "median_time_s", "fit_x"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nSaved time complexity CSV: {csv_path}")

    grouped: Dict[Tuple[str, str], List[Dict]] = {}
    for r in rows:
        # Fit each (algorithm, scenario) series separately.
        grouped.setdefault((r["algorithm"], r["scenario"]), []).append(r)

    print("\n[Time complexity fit] Models:")
    print("  build_heap : T(n) ~ a*n + b")
    print("  heapsort / maxheap_insert_extract : T(n) ~ a*(n log2 n) + b")
    fit_summary: List[Dict] = []
    for (algo, scen), rs in sorted(grouped.items()):
        rs.sort(key=lambda d: d["n"])
        x = [float(r["fit_x"]) for r in rs]
        y = [float(r["median_time_s"]) for r in rs]
        a, b, r2 = _linear_fit(x, y)
        fit_summary.append(
            {"algorithm": algo, "scenario": scen, "a": a, "b": b, "r2": r2}
        )
        print(f"  {algo:22s} | {scen:13s} | R^2={r2:.4f}")

    try:
        import matplotlib.pyplot as plt  # type: ignore

        def plot_fit_points(out_png: str, title: str, x: List[float], y: List[float], a: float, b: float, r2: float) -> None:
            x_min, x_max = min(x), max(x)
            plt.figure(figsize=(10, 5.5))
            plt.plot(x, y, "o", markersize=8, label="median T(n)")
            plt.plot([x_min, x_max], [a * x_min + b, a * x_max + b], "-", linewidth=2, label="fit")
            plt.title(f"{title}\n$R^2$={r2:.4f}", fontsize=15)
            if "build_heap" in title:
                plt.xlabel("x = n", fontsize=13)
            else:
                plt.xlabel(r"$x = n \cdot \log_2(n)$", fontsize=13)
            plt.ylabel("median time (seconds)", fontsize=13)
            plt.tick_params(axis="both", labelsize=12)
            plt.grid(True, alpha=0.25)
            plt.legend(fontsize=12)
            plt.tight_layout()
            plt.savefig(out_png, dpi=300)
            plt.close()

        for (algo, scen), rs in grouped.items():
            rs.sort(key=lambda d: d["n"])
            x = [float(r["fit_x"]) for r in rs]
            y = [float(r["median_time_s"]) for r in rs]
            a, b, r2 = _linear_fit(x, y)
            out_png = os.path.join(out_dir, f"time_complexity_fit_{algo}_{scen}.png")
            plot_fit_points(out_png, f"{algo} input distribution='{scen}'", x, y, a, b, r2)

        labels = [f"{a}/{s}" for a, s in [(d["algorithm"], d["scenario"]) for d in fit_summary]]
        r2s = [d["r2"] for d in fit_summary]
        plt.figure(figsize=(12, 5.5))
        ax_r2 = plt.gca()
        ax_r2.spines["top"].set_visible(False)
        ax_r2.spines["right"].set_visible(False)
        plt.bar(range(len(r2s)), r2s, color="#2ca02c")
        plt.xticks(range(len(r2s)), labels, rotation=45, ha="right", fontsize=11)
        plt.ylim(0.0, 1.01)
        plt.tick_params(axis="y", labelsize=12)
        plt.title("Time complexity fit $R^2$ (higher is better)", fontsize=15)
        plt.ylabel("$R^2$", fontsize=13)
        plt.grid(True, axis="y", alpha=0.25)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "time_complexity_fit_r2.png"), dpi=300)
        plt.close()

        print(f"Saved time complexity fit graphs to: {out_dir}/")
    except Exception:
        print("Note: time complexity fit graphs were not exported because matplotlib is not available.")

    return rows
