import dataclasses
import unittest

from desync import desync


@dataclasses.dataclass
class Item:
    value: int


def inner(item):
    item.value += 1
    return item


@desync
def outer(items):
    for item in items:
        inner(item)


class TestFor(unittest.TestCase):
    def test_for(self):
        items = [Item(value) for value in range(10)]
        outer(items)
        self.assertSequenceEqual([Item(value + 1) for value in range(10)], items)
