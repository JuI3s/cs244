import unittest

from bloom_filter import BloomFilter, State
from typing import Union, Optional


class DontKnow:
    
    def __init__(self) -> None:
        pass
class StatefulBloomFilterCell:
    
    def __init__(self) -> None:
        self.state: Optional[State] = None
        self.refCount: int = 0 

    def add(self, state: State):
        self.refCount = self.refCount + 1
        self.set(state=state)
        
    def set(self, state: State):
        if self.state is None:
            self.state = state
        elif self.state != 
        self.state = state 

class StatefulBloomFilter(BloomFilter):

    def __init__(self, num_hash_func=4) -> None:
        super().__init__(num_hash_func)
        self.store = [None for _ in range(self.num_buckets)]


    def insertEntry(self, flow: str, state: State):
        # • Insertion. Hash the flow. If the cell counter is 0, write the new value and set the count to 1. If the cell value is DK, increment the count. If the cell value equals the flow value, increment the count. If the cell value does not equal the flow value, increment the count but change the cell to DK.
        hash_vals = self.computeHashVals(flow)
        for  
        return super().insertEntry(flow, state)

    def modifyEntry(self, flow: str, newState: State):
        # • Modify. Hash the flow. If the cell value is DK, leave it. If the current count is 1, change the cell value. If current count is exceeds 1, change the cell value to DK.

        return super().modifyEntry(flow, newState)

    def lookup(self, flow: str) -> State:
        # • Lookup. Check all cells associated with a flow. If all cell values are DK, return DK. If all cell values have value i or DK (and at least one cell has value i), return i. If there is more than one value in the cells, the item is not in the set.

        return super().lookup(flow)

    def deleteEntry(self, flow: str):
        # • Deletion. Hash the flow. If the count is 1, reset cell to 0. If the count it at least 1, decrement count, leaving the value or DK as is.
        return super().deleteEntry(flow)


class TestStatefulBloomFilter(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
