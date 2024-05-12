import unittest
from typing import Optional, Union

from bloom_filter import BloomFilter, State


class DontKnow:

    def __init__(self) -> None:
        pass


class StatefulBloomFilterCell:

    def __init__(self) -> None:
        self.state = None
        self.refCount = 0

    def add(self, state):
        self.refCount = self.refCount + 1
        self.set(state=state)

    def set(self, state):
        if self.state is None:
            self.state = state
        elif self.state != DontKnow() and self.state != state:
            self.state = DontKnow()
        # self.tate must already be equal to state
        return

    def decrement(self):
        self.refCount = self.refCount - 1
        if self.refCount == 0:
            self.state = None


class StatefulBloomFilter(BloomFilter):

    def __init__(self, hash_count=4, num_cells=10) -> None:
        super().__init__(hash_count, num_cells=num_cells)
        self.store = [StatefulBloomFilterCell() for _ in range(self.num_buckets)]

    def insert_entry(self, flow, state):
        # • Insertion. Hash the flow. If the cell counter is 0, write the new value and set the count to 1. If the cell value is DK, increment the count. If the cell value equals the flow value, increment the count. If the cell value does not equal the flow value, increment the count but change the cell to DK.
        for hash_val in self.compute_hash_vals(flow):
            self.store[hash_val].add(state=state)

    def modify_entry(self, flow, state):
        # • Modify. Hash the flow. If the cell value is DK, leave it. If the current count is 1, change the cell value. If current count is exceeds 1, change the cell value to DK.
        for hash_val in self.compute_hash_vals(flow):
            self.store[hash_val].set(state=state)

    def lookup_entry(self, flow):
        # • Lookup. Check all cells associated with a flow. If all cell values are DK, return DK. If all cell values have value i or DK (and at least one cell has value i), return i. If there is more than one value in the cells, the item is not in the set.
        ret = None
        for hash_val in self.compute_hash_vals(flow):
            state = self.store[hash_val]

            if state is None:
                return None

            if ret is None:
                ret = state
            elif isinstance(ret, DontKnow) and not isinstance(state, DontKnow):
                ret = state
            elif ret != state and not isinstance(state, DontKnow):
                return None

        return ret if not isinstance(ret, DontKnow) else "IDK"

    def delete_entry(self, flow):
        # • Deletion. Hash the flow. If the count is 1, reset cell to 0. If the count it at least 1, decrement count, leaving the value or DK as is.
        for hash_val in self.compute_hash_vals(flow):
            self.store[hash_val].decrement()


class TestStatefulBloomFilter(unittest.TestCase):
    def test_stateful_bloom_filter_cell(self):
        cell = StatefulBloomFilterCell()
        self.assertEqual(cell.refCount, 0)
        self.assertEqual(cell.state, None)

        cell.add("one")
        self.assertEqual(cell.refCount, 1)
        self.assertEqual(cell.state, "one")

        cell.add("one")
        self.assertEqual(cell.refCount, 2)
        self.assertEqual(cell.state, "one")

        cell.set("two")
        self.assertEqual(cell.refCount, 2)
        self.assertTrue(isinstance(cell.state, DontKnow))

        cell.decrement()
        self.assertEqual(cell.refCount, 1)
        self.assertTrue(isinstance(cell.state, DontKnow))

        cell.decrement()
        self.assertEqual(cell.refCount, 0)
        self.assertIsNone(cell.state)


if __name__ == "__main__":
    unittest.main()
