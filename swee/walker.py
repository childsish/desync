import ast
import asyncio
import functools

from concurrent.futures import ThreadPoolExecutor
from operator import mod
from swee.futuretools import ensure_future, is_future
from swee.resolver import resolve
from typing import Sequence, Union


class Walker:
    def __init__(self, scopes):
        self._scopes = scopes
        self._tasks = []
        self._executor = ThreadPoolExecutor(4)

    def eval_node(self, node):
        if isinstance(node, ast.Assign):
            self.eval_assign(node)
        elif isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            return self.eval_functiondef(node)
        elif isinstance(node, ast.Await):
            return self.eval_await(node)
        elif isinstance(node, ast.BinOp):
            return self.eval_binop(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Constant):
            return self.eval_constant(node)
        elif isinstance(node, ast.Expr):
            return self.eval_expr(node)
        elif isinstance(node, ast.IfExp):
            return self.eval_ifexp(node)
        elif isinstance(node, ast.ListComp):
            return self.eval_listcomp(node)
        elif isinstance(node, ast.Name):
            return self.eval_name(node)
        elif isinstance(node, ast.Return):
            return self.eval_return(node)
        else:
            raise NotImplementedError(f'eval_node not implemented for {node}')

    def eval_assign(self, node: ast.Assign):
        value = self.eval_node(node.value)
        assert len(node.targets) != 0
        if len(node.targets) > 1:
            for target in node.targets:
                self.set_value(target.id, ensure_future(value))
        else:
            self.assign(node.targets[0], ensure_future(value))

    def eval_await(self, node: ast.Await):
        task = asyncio.create_task(eval_call(self.eval_node(node.value)))
        self._tasks.append(task)
        return task

    def eval_binop(self, node: ast.BinOp):
        left = self.eval_node(node.left)
        right = self.eval_node(node.right)
        op = mod if isinstance(node.op, ast.Mod) else None
        task = asyncio.create_task(eval_call(op, [left, right]))
        self._tasks.append(task)
        return task

    def eval_call(self, node: ast.Call):
        task = asyncio.create_task(eval_call(
            self.eval_node(node.func),
            [self.eval_node(arg) for arg in node.args],
            [self.eval_node(keyword) for keyword in node.keywords],
            self._executor,
        ))
        self._tasks.append(task)
        return task

    def eval_constant(self, node: ast.Constant):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        future.set_result(node.value)
        return future

    def eval_expr(self, node: ast.Expr):
        return self.eval_node(node.value)

    def eval_functiondef(self, node: ast.FunctionDef):
        res = None
        for statement in node.body:
            res = self.eval_node(statement)
        return res

    def eval_ifexp(self, node: ast.IfExp):
        test = self.eval_node(node.test)
        body = node.body
        orelse = node.orelse
        task = asyncio.create_task(eval_ifexp(test, body, orelse, self.copy_scopes()))
        self._tasks.append(task)
        return task

    def eval_listcomp(self, node: ast.ListComp):
        if len(node.generators) != 1:
            raise NotImplementedError
        generator = node.generators[0]
        items = self.eval_node(generator.iter)
        task = asyncio.create_task(eval_listcomp(items, generator.target, node.elt, self.copy_scopes()))
        self._tasks.append(task)
        return task

    def eval_name(self, node: ast.Name):
        for scope in self._scopes[::-1]:
            if node.id in scope:
                return scope[node.id]
        return __builtins__[node.id]

    def eval_return(self, node: ast.Return):
        return self.eval_node(node.value)

    def assign(self, target, value):
        if not isinstance(target, (ast.Tuple, ast.List)):
            self.set_value(target.id, ensure_future(value))
        else:
            if is_future(value):
                loop = asyncio.get_running_loop()
                futures = [loop.create_future() for _ in target.elts]
                self._tasks.append(asyncio.create_task(eval_assign(futures, value)))
            else:
                futures = [ensure_future(subvalue) for subvalue in value]

            for elt, future in zip(target.elts, futures):
                self.set_value(elt.id, future)

    def copy_scopes(self):
        return [scope for scope in self._scopes]

    def get_value(self, key):
        return self._scopes[-1][key]

    def set_value(self, key, value):
        self._scopes[-1][key] = value

    async def join(self):
        await asyncio.gather(*self._tasks)


async def eval_assign(futures: Sequence[asyncio.Future], values: Union[asyncio.Future, asyncio.Task]):
    await values
    for future, value in zip(futures, values.result()):
        future.set_result()


async def eval_call(func, pre_args=None, pre_kwargs=None, executor=None):
    if pre_args is None:
        args = []
    else:
        args = await resolve(pre_args)

    if pre_kwargs is None:
        kwargs = {}
    else:
        kwargs = {key: value.result() for key, value in await resolve(pre_kwargs)}

    loop = asyncio.get_running_loop()
    partial_func = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(executor, partial_func)


async def eval_ifexp(test_future, body, orelse, scopes):
    test = await test_future
    walker = Walker(scopes)
    return walker.eval_node(body) if test else walker.eval_node(orelse)


async def eval_listcomp(items_future, target, elt, scopes):
    items = await items_future
    walker = Walker(scopes)
    res = []
    scopes.append({})
    for item in items:
        walker.assign(target, item)
        res.append(walker.eval_node(elt))
    scopes.pop()
    return res
