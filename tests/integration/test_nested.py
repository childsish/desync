import unittest

from desync import desync


def inner(item):
    return item + 1


@desync
def outer1(item):
    return inner(item)


@desync
def outer2(item):
    return outer1(item)


class TestNested(unittest.TestCase):
    def test_nested(self):
        self.assertEqual(1, outer2(0))
