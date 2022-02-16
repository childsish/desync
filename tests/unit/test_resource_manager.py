import unittest

from desync.resource_manager import ResourceManager


class ResourceManagerTest(unittest.TestCase):
    def test_request(self):
        resource_manager = ResourceManager(cpus=64)
        with resource_manager.request(cpus=32) as resources:
            self.assertEqual(32, resources['cpus'])
            with self.assertRaises(ValueError):
                with resource_manager.request(cpus=33):
                    pass
        with self.assertRaises(ValueError):
            with resource_manager.request(cpus=65):
                pass

    def test_request_min(self):
        resource_manager = ResourceManager(cpus=64)
        with resource_manager.request(min_cpus=32) as resources:
            self.assertEqual(64, resources['cpus'])
            with self.assertRaises(ValueError):
                with resource_manager.request(min_cpus=1):
                    pass
        with resource_manager.request(min_cpus=32) as resources:
            self.assertEqual(64, resources['cpus'])
            with self.assertRaises(ValueError):
                with resource_manager.request(min_cpus=1):
                    pass
        with resource_manager.request(cpus=16) as outer_resources:
            self.assertEqual(16, outer_resources['cpus'])
            with resource_manager.request(min_cpus=32) as inner_resources:
                self.assertEqual(48, inner_resources['cpus'])
                with self.assertRaises(ValueError):
                    with resource_manager.request(min_cpus=1):
                        pass
        with self.assertRaises(ValueError):
            with resource_manager.request(min_cpus=65):
                pass

    def test_request_max(self):
        resource_manager = ResourceManager(cpus=64)
        with resource_manager.request(max_cpus=128) as resources:
            self.assertEqual(64, resources['cpus'])
