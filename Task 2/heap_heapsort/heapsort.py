"""
In-place max-heap and heapsort on a list.

``heapify(arr, n, i)`` treats ``arr[0:n]`` as a heap; only indices < n participate.
``heap_sort`` sorts the whole list ascending using a max-heap on the shrinking prefix.
"""


def heapify(arr, n, i, trace: bool = False, _depth: int = 0, swap_recorder=None):
    """Sift-down at index i: ensure subtree root i is >= its children inside [0, n)."""
    # Choose the largest among node i and its two children (if inside the heap).
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2

    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right

    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        if trace:
            indent = "  " * _depth
            print(f"{indent}[heapsort] heapify swap idx {i} <-> {largest}: {arr}")
        if swap_recorder is not None:
            swap_recorder(i, largest)
        # Recurse on the child that received the parent value.
        heapify(arr, n, largest, trace=trace, _depth=_depth + 1, swap_recorder=swap_recorder)


def build_max_heap(arr, trace: bool = False):
    """Floyd: heapify from last non-leaf upward. O(n)."""
    # Last parent index is (n//2 - 1); leaves need no heapify.
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        if trace:
            print(f"\n[heapsort] build_max_heap: heapify at i={i}, arr={arr}")
        heapify(arr, n, i, trace=trace)


def heap_sort(arr, trace: bool = False):
    """Sort ascending in-place."""
    # After build_max_heap, arr[0] is max. Swap it to arr[end], heapify prefix [0:end).
    n = len(arr)
    if trace:
        print(f"\n[heapsort] start heap_sort, arr={arr}")
    build_max_heap(arr, trace=trace)
    if trace:
        print(f"\n[heapsort] max-heap built: {arr}")
    for end in range(n - 1, 0, -1):
        if trace:
            print(f"\n[heapsort] move max to end: swap root with end={end}")
        arr[0], arr[end] = arr[end], arr[0]
        if trace:
            print(f"[heapsort] after root/end swap: {arr}")
        # Heap size is now ``end``; arr[end:] is sorted low to high at the tail.
        heapify(arr, end, 0, trace=trace)
    return arr
