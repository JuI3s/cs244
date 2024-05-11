import unittest

from bloom_filter import BloomFilter, State


class StatefulBloomFilter(BloomFilter):

    def __init__(self, num_hash_func=4) -> None:
        super().__init__(num_hash_func)

    def insertEntry(self, flow: str, state: State):
        return super().insertEntry(flow, state)

    def modifyEntry(self, flow: str, newState: State):
        return super().modifyEntry(flow, newState)

    def lookup(self, flow: str) -> State:
        return super().lookup(flow)

    def deleteEntry(self, flow: str):
        return super().deleteEntry(flow)


class TestStatefulBloomFilter(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
