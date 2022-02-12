import unittest

from swee import desync


def poke(item):
    return item + 1


def prod(item):
    return item // 2


@desync
def outer(items):
    poked_and_prodded = [poke(item) if item % 2 else prod(item) for item in items]
    return 'poked' if sum(poked_and_prodded) % 2 else 'prodded'


class TestListcomp(unittest.TestCase):
    def test_listcomp(self):
        self.assertEqual('prodded', outer(range(10)))
        self.assertEqual('poked', outer(range(11)))
