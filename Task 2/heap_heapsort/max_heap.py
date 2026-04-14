"""
Array-based binary max-heap.

The tree is stored in level order: index 0 is the root, and for any node i:
  parent(i) = (i - 1) // 2,  left(i) = 2*i + 1,  right(i) = 2*i + 2.
Max-heap rule: each value is >= its children (where they exist).
"""


class MaxHeap:
    """Max-heap with O(log n) insert (swim-up) and extract_max (sink-down)."""

    def __init__(self, trace: bool = False, swap_recorder=None):
        self.heap = []  # level-order list; largest element is always heap[0]
        self.trace = trace
        # Optional callback(i, j) so diagrams/tables can log each swap index pair.
        self._swap_recorder = swap_recorder

    def parent(self, i):
        return (i - 1) // 2

    def left_child(self, i):
        return 2 * i + 1

    def right_child(self, i):
        return 2 * i + 2

    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        if self._swap_recorder is not None:
            self._swap_recorder(i, j)

    def insert(self, value):
        if self.trace:
            print(f"\n[MaxHeap] insert {value}")
        insert_idx = len(self.heap)
        self.heap.append(value)
        # Dummy (i,i) notifies exporters that a new leaf appeared at insert_idx.
        if self._swap_recorder is not None:
            self._swap_recorder(insert_idx, insert_idx)
        self._swim_up(len(self.heap) - 1)
        if self.trace:
            print(f"[MaxHeap] after insert: {self.heap}")

    def _swim_up(self, index):
        # Fix heap after insert: swap with parent while parent is smaller.
        while index > 0 and self.heap[self.parent(index)] < self.heap[index]:
            p = self.parent(index)
            if self.trace:
                print(f"[MaxHeap] swim_up swap idx {index} <-> parent {p}")
            self.swap(index, p)
            index = p

    def extract_max(self):
        # Standard PQ extract: take root, put last leaf at root, sink it down.
        if not self.heap:
            raise IndexError("Extract from empty heap")
        if len(self.heap) == 1:
            if self.trace:
                print(f"\n[MaxHeap] extract_max -> {self.heap[0]} (last element)")
            if self._swap_recorder is not None:
                self._swap_recorder(0, 0)
            return self.heap.pop()

        max_value = self.heap[0]
        if self.trace:
            print(f"\n[MaxHeap] extract_max (root={max_value})")
        if self._swap_recorder is not None:
            last_index = len(self.heap) - 1
            # Mark root and tail for step-by-step exports before the structural change.
            self._swap_recorder(0, 0)
            self._swap_recorder(last_index, last_index)
        self.heap[0] = self.heap.pop()
        self._sink_down(0)
        if self.trace:
            print(f"[MaxHeap] after extract: {self.heap}")
        return max_value

    def _sink_down(self, index):
        # Fix heap after extract: repeatedly swap with the larger child until stable.
        size = len(self.heap)
        while self.left_child(index) < size:
            larger_child = self.left_child(index)
            right = self.right_child(index)
            if right < size and self.heap[right] > self.heap[larger_child]:
                larger_child = right

            if self.heap[index] >= self.heap[larger_child]:
                break  # max-heap property holds at this node
            if self.trace:
                print(f"[MaxHeap] sink_down swap idx {index} <-> child {larger_child}")
            self.swap(index, larger_child)
            index = larger_child

    def peek(self):
        if not self.heap:
            raise IndexError("Peek from empty heap")
        return self.heap[0]

    def is_empty(self):
        return len(self.heap) == 0
