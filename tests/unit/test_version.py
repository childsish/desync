from desync.version import Version
from unittest import TestCase


class TestVersion(TestCase):
    def test_no_update(self):
        old_version = Version(1, (0, 0))
        new_version = Version(1, (0, 0))
        new_version.set_old_version(old_version)

        self.assertEqual('1.0', str(new_version))

    def test_minor_update(self):
        old_version = Version(1, (0, 0))
        new_version = Version(1, (0, 1))
        new_version.set_old_version(old_version)

        self.assertEqual('1.1', str(new_version))

    def test_major_update(self):
        old_version = Version(1, (0, 0))
        new_version = Version(2, (0, 0))
        new_version.set_old_version(old_version)

        self.assertEqual('2.0', str(new_version))

    def test_update_both(self):
        old_version = Version(1, (0, 0))
        new_version = Version(2, (0, 0))
        new_version.set_old_version(old_version)

        self.assertEqual('2.0', str(new_version))

    def test_input_changes(self):
        old_version = Version(1, (0, 0))
        new_version = Version(1, (0, 0))
        new_version.set_old_version(old_version)

        self.assertEqual('1.0', str(new_version))
