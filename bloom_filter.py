import unittest

from abc import abstractmethod
from enum import auto, Enum

import xxhash


xxhash.xxh64("xxhash", seed=20141025)


class State(Enum):
    pass


class BloomFilter:

    def __init__(self, num_hash_func=4) -> None:
        self.seeds = []
        self.num_hash_func = num_hash_func
        self.setupHashFunc()

    def computeHashVals(self, val: str) -> list[int]:
        return [xxhash.xxh64(val, seed=seed).intdigest() for seed in self.seeds]

    def setupHashFunc(self):
        for i in range(self.num_hash_func):
            self.seeds.append(i)

    @abstractmethod
    def insertEntry(self, flow: str, state: State):
        pass

    @abstractmethod
    def modifyEntry(self, flow: str, newState: State):
        pass

    @abstractmethod
    def lookup(self, flow: str) -> State:
        pass

    @abstractmethod
    def deleteEntry(self, flow: str):
        pass


class TestBloomFiltersMethods(unittest.TestCase):

    def test_hash_deterministic(self):
        filter = BloomFilter()
        self.assertEqual(len(filter.computeHashVals("hello_world")), 4)
        self.assertEqual(
            filter.computeHashVals("hello_world"), filter.computeHashVals("hello_world")
        )
        self.assertNotEqual(
            filter.computeHashVals("val1"), filter.computeHashVals("val2")
        )


if __name__ == "__main__":
    unittest.main()
