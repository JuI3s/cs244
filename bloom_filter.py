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

    def __init__(self, hash_count=4, num_cells=10):
        self.seeds = []
        self.num_hash_func = hash_count
        self.num_buckets = num_cells
        self.setupHashFunc()

    def compute_hash_vals(self, val, modulo_to_buckets=True):
        ret = [xxhash.xxh64(val, seed=seed).intdigest() for seed in self.seeds]
        ret = [each % self.num_buckets if modulo_to_buckets else each for each in ret]
        return ret

    def setupHashFunc(self):
        for i in range(self.num_hash_func):
            self.seeds.append(i)

    @abstractmethod
    def insert_entry(self, flow, state):
        pass

    @abstractmethod
    def modify_entry(self, flow, newState):
        pass

    @abstractmethod
    def lookup(self, flow):
        pass

    @abstractmethod
    def delete_entry(self, flow):
        pass


class TestBloomFiltersMethods(unittest.TestCase):

    def test_hash_deterministic(self):
        filter = BloomFilter()
        self.assertEqual(
            len(filter.compute_hash_vals("hello_world", modulo_to_buckets=False)), 4
        )
        self.assertEqual(
            filter.compute_hash_vals("hello_world", modulo_to_buckets=False),
            filter.compute_hash_vals("hello_world", modulo_to_buckets=False),
        )
        self.assertNotEqual(
            filter.compute_hash_vals("val1", modulo_to_buckets=False),
            filter.compute_hash_vals("val2", modulo_to_buckets=False),
        )

    def test_hash_to_buckets(self):
        filter = BloomFilter()
        hash_vals = filter.compute_hash_vals("hello_world")
        self.assertTupleEqual(
            tuple([0 <= each and each <= filter.num_buckets for each in hash_vals]),
            tuple([True for _ in range(len(hash_vals))]),
        )


if __name__ == "__main__":
    unittest.main()
