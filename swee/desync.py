import ast
import asyncio

from swee.cache import Cache
from swee.function import Function
from swee.futuretools import ensure_future
from swee.resolver import resolve
from swee.version import Version
from swee.walker import Walker


class Desync:
    def __init__(self, func):
        self._func = Function(func)
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
            self._func.get_ast().__dict__,
            {key: ensure_future(args[i]) if i < len(args) else ensure_future(kwargs[key])
             for i, key in enumerate(self._func.get_signature().parameters)},
        ]
        walker = Walker(scopes)
        tree = ast.parse(self._func.get_source())
        return walker.eval_node(tree.body[0])

    @property
    def name(self):
        return self._func.name

    def set_version(self, version):
        self._version.set_old_version(version)

    def get_version(self):
        return self._version

    def set_cache(self, cache):
        self._old_cache = cache

    def get_cache(self):
        return self._new_cache

    async def run_outer_workflow(self, args, kwargs):
        scopes = [
            self._func.get_module().__dict__,
            {key: ensure_future(args[i]) if i < len(args) else ensure_future(kwargs[key])
             for i, key in enumerate(self._func.get_signature().parameters)},
        ]
        walker = Walker(scopes)
        tree = self._func.get_ast()
        res = walker.eval_node(tree.body[0])
        await walker.join()
        return await resolve(res)


def desync(func):
    return Desync(func)
