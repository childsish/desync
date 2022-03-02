import unittest

from desync import desync


def poke(item):
    return item + 1


def prod(item):
    return item // 2


@desync
def outer(items):
    if len(items) % 2:
        return [poke(item) for item in items]
    else:
        return [prod(item) for item in items]


class TestIf(unittest.TestCase):
    def test_if(self):
        self.assertListEqual([0, 0, 1, 1, 2, 2, 3, 3, 4, 4], outer(range(10)))
        self.assertListEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], outer(range(11)))
