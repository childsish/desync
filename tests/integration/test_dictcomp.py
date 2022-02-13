import unittest

from desync import desync


def inner(item):
    return item + 1


@desync
def outer(items1):
    items2 = {item1: inner(item1) for item1 in items1}
    items3 = {item2: inner(item2) for item2 in items2.values()}
    return {item3: inner(item3) for item3 in items3.values()}


class TestDictcomp(unittest.TestCase):
    def test_dictcomp(self):
        result = outer(range(10))
        self.assertSetEqual(set(x + 3 for x in range(10)), set(result.values()))
