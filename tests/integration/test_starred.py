import unittest

from swee import desync


def inner_args(a, b, c):
    return a, b, c


def inner_kwargs(a, b, c):
    return a, b, c


@desync
def outer(items):
    kwargs = {key: value for key, value in zip('abc', inner_args(*items))}
    return inner_kwargs(**kwargs)


class TestStarred(unittest.TestCase):
    def test_starred(self):
        self.assertSequenceEqual((0, 1, 2), outer((0, 1, 2)))
