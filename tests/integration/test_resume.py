import dataclasses
import unittest

from swee import desync
from swee.version import Version
from typing import Sequence


@dataclasses.dataclass
class Object:
    value: int
    is_first_run_object: bool

    def __repr__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other.value


def step1(a: Object) -> Object:
    a.value += 1
    return a


def step2(a: Object) -> Object:
    a.value += 2
    return a


def step3(a: Object) -> Object:
    a.value += 3
    return a


def step4(a: Object) -> Object:
    a.value += 10
    return a


@desync
def version1(items1: Sequence[Object]) -> Object:
    items2 = [step1(item) for item in items1]
    items3 = [step2(item) for item in items2]
    return [step3(item) for item in items3]


@desync
def version2(items1: Sequence[Object]) -> Object:
    items2 = [step1(item) for item in items1]
    items3 = [step2(item) for item in items2]
    return [step4(item) for item in items3]


class TestResume(unittest.TestCase):
    def test_same_workflow(self):
        old_version = Version(version1.get_version().major_hash, version1.get_version().minor_hash)
        self.assertEqual('1.0', str(old_version))
        version1.set_version(old_version)
        self.assertEqual('1.0', str(version1.get_version()))

        a = sorted(
            version1([Object(value, True) for value in range(10)]),
            key=lambda item: item.value)
        version1.set_cache(version1.get_cache())
        b = sorted(
            version1([Object(value, False) for value in range(10)]),
            key=lambda item: item.value)
        self.assertSequenceEqual([Object(i + 6, True) for i in range(10)], a)
        self.assertSequenceEqual([Object(i + 6, True) for i in range(10)], b)

    def test_step_changed(self):
        old_version = Version(version2.get_version().major_hash, version1.get_version().minor_hash)
        self.assertEqual('1.0', str(old_version))
        version2.set_version(old_version)
        self.assertEqual('1.1', str(version2.get_version()))

        a = sorted(
            version1([Object(value, True) for value in range(10)]),
            key=lambda item: item.value)
        version2.set_cache(version1.get_cache())
        b = sorted(
            version2([Object(value, False) for value in range(10)]),
            key=lambda item: item.value)
        self.assertSequenceEqual([Object(i + 6, True) for i in range(10)], a)
        self.assertSequenceEqual([Object(i + 13, True) for i in range(10)], b)
