import unittest
from typing import Optional, Union

from bloom_filter import BloomFilter, State


class DontKnow:

    def __init__(self) -> None:
        pass


class StatefulBloomFilterCell:

    def __init__(self) -> None:
        self.state: Optional[Union[State, DontKnow]] = None
        self.refCount: int = 0

    def add(self, state: State):
        self.refCount = self.refCount + 1
        self.set(state=state)

    def set(self, state: State):
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

    def __init__(self, num_hash_func=4) -> None:
        super().__init__(num_hash_func)
        self.store = [StatefulBloomFilterCell() for _ in range(self.num_buckets)]

    def insertEntry(self, flow: str, state: State):
        # • Insertion. Hash the flow. If the cell counter is 0, write the new value and set the count to 1. If the cell value is DK, increment the count. If the cell value equals the flow value, increment the count. If the cell value does not equal the flow value, increment the count but change the cell to DK.
        for hash_val in self.computeHashVals(flow):
            self.store[hash_val].add(state=state)

    def modifyEntry(self, flow: str, state: State):
        # • Modify. Hash the flow. If the cell value is DK, leave it. If the current count is 1, change the cell value. If current count is exceeds 1, change the cell value to DK.
        for hash_val in self.computeHashVals(flow):
            self.store[hash_val].set(state=state)

    def lookup(self, flow: str) -> Optional[State]:
        # • Lookup. Check all cells associated with a flow. If all cell values are DK, return DK. If all cell values have value i or DK (and at least one cell has value i), return i. If there is more than one value in the cells, the item is not in the set.
        ret = None
        for hash_val in self.computeHashVals(flow):
            state = self.store[hash_val]

            if state is None:
                return None

            if ret is None:
                ret = state
            elif isinstance(ret, DontKnow) and not isinstance(state, DontKnow):
                ret = state
            elif ret != state and not isinstance(state, DontKnow):
                return None

        return ret

    def deleteEntry(self, flow: str):
        # • Deletion. Hash the flow. If the count is 1, reset cell to 0. If the count it at least 1, decrement count, leaving the value or DK as is.
        for hash_val in self.computeHashVals(flow):
            self.store[hash_val].decrement()


class TestStatefulBloomFilter(unittest.TestCase):
    def test_stateful_bloom_filter_cell(self):
        cell = StatefulBloomFilterCell()
        self.assertEqual(cell.refCount, 0)
        self.assertEqual(cell.state, None)

        cell.add(State.one)
        self.assertEqual(cell.refCount, 1)
        self.assertEqual(cell.state, State.one)

        cell.add(State.one)
        self.assertEqual(cell.refCount, 2)
        self.assertEqual(cell.state, State.one)

        cell.set(State.two)
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
