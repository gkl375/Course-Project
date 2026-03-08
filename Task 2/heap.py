class MaxHeap:
    """
    Implementation of Max-Heap data structure.
    """
    def __init__(self):
        self.heap = []

    def parent(self, i):
        """Return parent index of node at index i"""
        return (i - 1) // 2

    def left_child(self, i):
        """Return left child index of node at index i"""
        return 2 * i + 1

    def right_child(self, i):
        """Return right child index of node at index i"""
        return 2 * i + 2

    def swap(self, i, j):
        """Swap elements at indices i and j"""
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, value):
        """
        Insert a new value into the heap.
        Time Complexity: O(log n)
        """
        self.heap.append(value)
        self._swim_up(len(self.heap) - 1)

    def _swim_up(self, index):
        """
        Restore heap property by swimming element up.
        Also called bubble-up or sift-up.
        """
        while index > 0 and self.heap[self.parent(index)] < self.heap[index]:
            self.swap(index, self.parent(index))
            index = self.parent(index)

    def extract_max(self):
        """
        Remove and return the maximum element (root).
        Time Complexity: O(log n)
        """
        if len(self.heap) == 0:
            raise IndexError("Extract from empty heap")

        if len(self.heap) == 1:
            return self.heap.pop()

        max_value = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._sink_down(0)
        return max_value

    def _sink_down(self, index):
        """
        Restore heap property by sinking element down.
        Also called bubble-down or sift-down.
        """
        size = len(self.heap)
        while self.left_child(index) < size:
            larger_child = self.left_child(index)
            right = self.right_child(index)

            # Find the larger child
            if right < size and self.heap[right] > self.heap[larger_child]:
                larger_child = right

            # If heap property is satisfied, stop
            if self.heap[index] >= self.heap[larger_child]:
                break

            self.swap(index, larger_child)
            index = larger_child

    def peek(self):
        """
        Return maximum element without removing it.
        Time Complexity: O(1)
        """
        if len(self.heap) == 0:
            raise IndexError("Peek from empty heap")
        return self.heap[0]

    def size(self):
        """Return the number of elements in heap"""
        return len(self.heap)

    def is_empty(self):
        """Check if heap is empty"""
        return len(self.heap) == 0