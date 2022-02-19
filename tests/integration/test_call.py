import unittest
import subprocess

from desync import desync


def inner_args(item):
    prc = subprocess.Popen(['ping', '-c', '2', '127.0.0.1'], stdout=subprocess.PIPE)
    prc.communicate()
    return item + 1


def inner_kwargs(*, item):
    prc = subprocess.Popen(['ping', '-c', '2', '127.0.0.1'], stdout=subprocess.PIPE)
    prc.communicate()
    return item + 1


@desync
def outer(item1):
    inner_args(item1)
    inner_args(item1)
    inner_args(item1)
    inner_args(item1)
    inner_kwargs(item=item1)
    item2 = inner_args(item1)
    return item2


class TestCall(unittest.TestCase):
    def test_call(self):
        self.assertEqual(1, outer(0))
