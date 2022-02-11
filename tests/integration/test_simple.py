import time
import unittest
import subprocess

from swee import desync


def inner(item):
    prc = subprocess.Popen(['ping', '-n', '2', '127.0.0.1'])
    prc.communicate()
    return item + 1


@desync
def outer(item1):
    inner(item1)
    inner(item1)
    item2 = inner(item1)
    return item2


class TestSimple(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(1, outer(0))
