import unittest

from abc import abstractmethod
from enum import auto, Enum
from typing import Optional

import xxhash


xxhash.xxh64("xxhash", seed=20141025)


class State(Enum):
    one = auto()
    two = auto()
    three = auto()


class BloomFilter:

    def __init__(self, num_hash_func=4, num_buckets=10) -> None:
        self.seeds = []
        self.num_hash_func = num_hash_func
        self.num_buckets = num_buckets
        self.setupHashFunc()

    def computeHashVals(self, val: str, modulo_to_buckets=True) -> list[int]:
        ret = [xxhash.xxh64(val, seed=seed).intdigest() for seed in self.seeds]
        ret = [each % self.num_buckets if modulo_to_buckets else each for each in ret]
        return ret

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
    def lookup(self, flow: str) -> Optional[State]:
        pass

    @abstractmethod
    def deleteEntry(self, flow: str):
        pass


class TestBloomFiltersMethods(unittest.TestCase):

    def test_hash_deterministic(self):
        filter = BloomFilter()
        self.assertEqual(
            len(filter.computeHashVals("hello_world", modulo_to_buckets=False)), 4
        )
        self.assertEqual(
            filter.computeHashVals("hello_world", modulo_to_buckets=False),
            filter.computeHashVals("hello_world", modulo_to_buckets=False),
        )
        self.assertNotEqual(
            filter.computeHashVals("val1", modulo_to_buckets=False),
            filter.computeHashVals("val2", modulo_to_buckets=False),
        )

    def test_hash_to_buckets(self):
        filter = BloomFilter()
        hash_vals = filter.computeHashVals("hello_world")
        self.assertTupleEqual(
            tuple([0 <= each and each <= filter.num_buckets for each in hash_vals]),
            tuple([True for _ in range(len(hash_vals))]),
        )


if __name__ == "__main__":
    unittest.main()
