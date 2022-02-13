from desync.cache import Cache
from unittest import TestCase


class TestCache(TestCase):
    def test_outputs(self):
        cache = Cache({
            0: {0: 0},
        })

        self.assertTrue(cache.has_outputs(0, 0))
        self.assertFalse(cache.has_outputs(0, 1))
        self.assertFalse(cache.has_outputs(1, 0))
        self.assertEqual(0, cache.get_outputs(0, 0))

        cache.set_outputs(0, 1, 0)
        self.assertTrue(cache.has_outputs(0, 1))
        self.assertEqual(0, cache.get_outputs(0, 1))
