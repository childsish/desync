import ast
import asyncio
import inspect

from swee.futuretools import ensure_future
from swee.walker import Walker


def desync(func):
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            return asyncio.run(run_outer_workflow(args, kwargs))

        scopes = [
            inspect.getmodule(func).__dict__,
            {key: ensure_future(args[i]) if i < len(args) else ensure_future(kwargs[key])
             for i, key in enumerate(inspect.signature(func).parameters)},
        ]
        walker = Walker(scopes)
        tree = ast.parse(inspect.getsource(func))
        return walker.eval_node(tree.body[0])

    async def run_outer_workflow(args, kwargs):
        scopes = [
            inspect.getmodule(func).__dict__,
            {key: ensure_future(args[i]) if i < len(args) else ensure_future(kwargs[key])
             for i, key in enumerate(inspect.signature(func).parameters)},
        ]
        walker = Walker(scopes)
        tree = ast.parse(inspect.getsource(func))
        res = walker.eval_node(tree.body[0])
        await walker.join()
        return await resolve(res)

    async def resolve(res):
        while inspect.isawaitable(res):
            res = await resolve_future(res)
        if isinstance(res, (list, tuple)):
            res = await resolve_sequence(res)
        return res

    async def resolve_future(future):
        return await future

    async def resolve_sequence(sequence):
        return [await resolve(item) for item in sequence]

    return wrapper
