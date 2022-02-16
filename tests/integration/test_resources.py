import unittest
import subprocess

from desync import desync, ResourceManager


RANK = 1


def inner(cpus, resource_manager: ResourceManager):
    global RANK
    with resource_manager.request(cpus=cpus):
        prc = subprocess.Popen(['ping', '-n', '3', '127.0.0.1'], stdout=subprocess.PIPE)
        prc.communicate()
    rank = RANK
    RANK += 1
    return rank, cpus


@desync
def outer(resource_manager):
    return {
        inner(1, resource_manager),
        inner(4, resource_manager),
        inner(1, resource_manager),
        inner(1, resource_manager),
        inner(1, resource_manager)
    }


class TestCall(unittest.TestCase):
    def test_call(self):
        resource_manager = ResourceManager(cpus=4)
        self.assertSetEqual({(1, 1), (2, 1), (3, 1), (4, 1), (5, 4)}, outer(resource_manager))
