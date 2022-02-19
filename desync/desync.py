import ast
import asyncio
import pickle

from concurrent.futures import ThreadPoolExecutor
from desync.cache import Cache
from desync.function import Function
from desync.futuretools import ensure_future
from desync.resolver import resolve
from desync.version import Version
from desync.walker import Walker
from typing import Optional


class Desync:
    def __init__(self, func, executor: Optional[ThreadPoolExecutor] = None):
        self._func = Function(func)
        self._executor = executor
        self._version = Version(self._func.get_hash(), self._func.get_step_hashes())
        self._old_cache = Cache()
        self._new_cache = Cache()

    def __call__(self, *args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            return asyncio.run(self.run_outer_workflow(args, kwargs))

        scopes = [
            self._func.get_module().__dict__,
            {key: ensure_future(args[i]) if i < len(args) else ensure_future(kwargs[key])
             for i, key in enumerate(self._func.get_signature().parameters)},
        ]
        walker = Walker(scopes, self._old_cache, self._new_cache)
        tree = ast.parse(self._func.get_source())
        return walker.eval_node(tree.body[0])

    @property
    def name(self):
        return self._func.name

    def set_version(self, version):
        self._version.set_old_version(version)

    def get_version(self):
        return self._version

    def load_version(self, fileobj):
        self.set_version(pickle.load(fileobj))

    def save_version(self, fileobj):
        pickle.dump(self.get_version(), fileobj)

    def set_cache(self, cache):
        self._old_cache = cache

    def get_cache(self):
        return self._new_cache

    def load_cache(self, fileobj):
        self.set_cache(pickle.load(fileobj))

    def save_cache(self, fileobj):
        pickle.dump(self.get_cache(), fileobj)

    async def run_outer_workflow(self, args, kwargs):
        if self._executor:
            loop = asyncio.get_running_loop()
            loop.set_default_executor(self._executor)

        scopes = [
            self._func.get_module().__dict__,
            {key: ensure_future(args[i]) if i < len(args) else ensure_future(kwargs[key])
             for i, key in enumerate(self._func.get_signature().parameters)},
        ]
        walker = Walker(scopes, self._old_cache, self._new_cache)
        tree = self._func.get_ast()
        res = walker.eval_node(tree.body[0])
        await walker.join()
        return await resolve(res)


def desync(func):
    return Desync(func)
