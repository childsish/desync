import time
import unittest
import subprocess

from swee import desync


def inner(item):
    prc = subprocess.Popen(['ping', '-n', '2', '127.0.0.1'], stdout=subprocess.PIPE)
    prc.communicate()
    return item + 1


@desync
def outer(items1):
    items2 = [inner(item1) for item1 in items1]
    items3 = [inner(item2) for item2 in items2]
    return [inner(item3) for item3 in items3]


class TestListcomp(unittest.TestCase):
    def test_listcomp(self):
        self.assertEqual([x + 3 for x in range(10)], outer(range(10)))
