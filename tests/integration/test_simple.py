import time
import unittest

from swee import desync


def inner(item):
    time.sleep(1)
    return item + 1


@desync
def outer(item1):
    item2 = inner(item1)
    item3 = inner(item2)
    return item3


class TestSimple(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(2, outer(0))
