import ast
import asyncio
import copy
import functools
import inspect

from operator import mod
from desync.cache import Cache
from desync.futuretools import ensure_future, is_future
from desync.hashtools import hash_function, hash_input
from desync.resolver import resolve
from typing import Optional, Sequence, Union


class Walker:
    def __init__(self, scopes, old_cache, new_cache):
        self._scopes = scopes
        self._tasks = []
        self._old_cache = old_cache
        self._new_cache = new_cache

    def eval_node(self, node):
        if isinstance(node, ast.Assign):
            self.eval_assign(node)
        elif isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            return self.eval_functiondef(node)
        elif isinstance(node, ast.Attribute):
            return self.eval_attribute(node)
        elif isinstance(node, ast.Await):
            return self.eval_await(node)
        elif isinstance(node, ast.BinOp):
            return self.eval_binop(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Constant):
            return self.eval_constant(node)
        elif isinstance(node, ast.DictComp):
            return self.eval_dictcomp(node)
        elif isinstance(node, ast.Expr):
            return self.eval_expr(node)
        elif isinstance(node, ast.For):
            return self.eval_for(node)
        elif isinstance(node, ast.If):
            return self.eval_if(node)
        elif isinstance(node, ast.IfExp):
            return self.eval_ifexp(node)
        elif isinstance(node, ast.List):
            return self.eval_list(node)
        elif isinstance(node, ast.ListComp):
            return self.eval_listcomp(node)
        elif isinstance(node, ast.Name):
            return self.eval_name(node)
        elif isinstance(node, ast.Num):
            return self.eval_num(node)
        elif isinstance(node, ast.Return):
            return self.eval_return(node)
        elif isinstance(node, ast.Set):
            return self.eval_set(node)
        elif isinstance(node, ast.Starred):
            return self.eval_starred(node)
        elif isinstance(node, ast.Tuple):
            return self.eval_tuple(node)
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

    def eval_attribute(self, node: ast.Attribute):
        task = asyncio.create_task(eval_attribute(self.eval_node(node.value), node.attr))
        self._tasks.append(task)
        return task

    def eval_await(self, node: ast.Await):
        task = asyncio.create_task(eval_call(ensure_future(self.eval_node(node.value))))
        self._tasks.append(task)
        return task

    def eval_binop(self, node: ast.BinOp):
        left = self.eval_node(node.left)
        right = self.eval_node(node.right)
        op = mod if isinstance(node.op, ast.Mod) else None
        task = asyncio.create_task(eval_call(
            ensure_future(op),
            [left, right],
            ast_args=[type(left), type(right)],
        ))
        self._tasks.append(task)
        return task

    def eval_call(self, node: ast.Call):
        task = asyncio.create_task(eval_call(
            ensure_future(self.eval_node(node.func)),
            [self.eval_node(arg) for arg in node.args],
            [self.eval_node(keyword.value) for keyword in node.keywords],
            ast_args=node.args,
            ast_kwargs=node.keywords,
            old_cache=self._old_cache,
            new_cache=self._new_cache,
        ))
        self._tasks.append(task)
        return task

    def eval_constant(self, node: ast.Constant):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        future.set_result(node.value)
        return future

    def eval_dictcomp(self, node: ast.DictComp):
        if len(node.generators) != 1:
            raise NotImplementedError
        generator = node.generators[0]
        items = self.eval_node(generator.iter)
        task = asyncio.create_task(eval_dictcomp(items, generator.target, node.key, node.value, self.copy_scopes(), self._old_cache, self._new_cache))
        self._tasks.append(task)
        return task

    def eval_expr(self, node: ast.Expr):
        return self.eval_node(node.value)

    def eval_for(self, node: ast.For):
        iter = self.eval_node(node.iter)
        task = asyncio.create_task(eval_for(iter, node.target, node.body, self.copy_scopes(), self._old_cache, self._new_cache))
        self._tasks.append(task)
        return task

    def eval_functiondef(self, node: ast.FunctionDef):
        res = None
        for statement in node.body:
            res = self.eval_node(statement)
        return res

    def eval_if(self, node: ast.If):
        test = self.eval_node(node.test)
        body = node.body
        orelse = node.orelse
        task = asyncio.create_task(eval_if(test, body, orelse, self.copy_scopes(), self._old_cache, self._new_cache))
        self._tasks.append(task)
        return task

    def eval_ifexp(self, node: ast.IfExp):
        test = self.eval_node(node.test)
        body = node.body
        orelse = node.orelse
        task = asyncio.create_task(eval_ifexp(test, body, orelse, self.copy_scopes(), self._old_cache, self._new_cache))
        self._tasks.append(task)
        return task

    def eval_list(self, node: ast.List):
        return [self.eval_node(elt) for elt in node.elts]

    def eval_listcomp(self, node: ast.ListComp):
        if len(node.generators) != 1:
            raise NotImplementedError
        generator = node.generators[0]
        items = self.eval_node(generator.iter)
        task = asyncio.create_task(eval_listcomp(items, generator.target, node.elt, self.copy_scopes(), self._old_cache, self._new_cache))
        self._tasks.append(task)
        return task

    def eval_name(self, node: ast.Name):
        for scope in self._scopes[::-1]:
            if node.id in scope:
                return scope[node.id]
        return __builtins__[node.id]

    def eval_num(self, node: ast.Num):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        future.set_result(node.n)
        return future

    def eval_return(self, node: ast.Return):
        return self.eval_node(node.value)

    def eval_set(self, node: ast.Set):
        return set(self.eval_node(elt) for elt in node.elts)

    def eval_starred(self, node: ast.Starred):
        return self.eval_node(node.value)

    def eval_tuple(self, node: ast.Tuple):
        return tuple(self.eval_node(elt) for elt in node.elts)

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
        future.set_result(value)


async def eval_attribute(value_future, attr):
    value = await ensure_future(value_future)
    return getattr(value, attr)


async def eval_call(
    func_future: asyncio.Future,
    pre_args=None,
    pre_kwargs=None,
    *,
    ast_args=None,
    ast_kwargs=None,
    old_cache: Optional[Cache] = None,
    new_cache: Optional[Cache] = None
):
    pre_args = [] if pre_args is None else pre_args
    pre_kwargs = [] if pre_kwargs is None else pre_kwargs
    ast_args = [type(arg) for arg in pre_args] if ast_args is None else ast_args
    ast_kwargs = [type(kwarg) for kwarg in pre_kwargs] if ast_kwargs is None else ast_kwargs

    args = []
    for ast_arg, pre_arg in zip(ast_args, await resolve(pre_args)):
        if isinstance(ast_arg, ast.Starred):
            args.extend(pre_arg)
        else:
            args.append(pre_arg)
    kwargs = {}
    for ast_kwarg, pre_kwarg in zip(ast_kwargs, pre_kwargs):
        value = await resolve(pre_kwarg)
        if ast_kwarg.arg is None:
            kwargs.update(value)
        else:
            kwargs[ast_kwarg.arg] = value
    loop = asyncio.get_running_loop()
    func = await func_future
    if inspect.isbuiltin(func) or type(func).__name__ == 'Desync' or func.__name__ in __builtins__:
        result = func(*args, **kwargs)
    else:
        try:
            func_hash = hash_function(func)
            input_hash = hash_input(args, kwargs)
            if old_cache and old_cache.has_outputs(func_hash, input_hash):
                result = old_cache.get_outputs(func_hash, input_hash)
            else:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    partial_func = functools.partial(func, *args, **kwargs)
                    result = await loop.run_in_executor(None, partial_func)
            if new_cache:
                new_cache.set_outputs(func_hash, input_hash, copy.deepcopy(result))
        except TypeError:
            result = func(*args, **kwargs)
    return result


async def eval_dictcomp(items_future, target, key, value, scopes, old_cache, new_cache):
    items = await resolve(items_future)
    walker = Walker(scopes, old_cache, new_cache)
    res = {}
    scopes.append({})
    for item in items:
        walker.assign(target, item)
        tmp = await resolve(walker.eval_node(key))
        res[tmp] = walker.eval_node(value)
    scopes.pop()
    return res


async def eval_for(iter_future, target, body, scopes, old_cache, new_cache):
    iter = await resolve(iter_future)
    walker = Walker(scopes, old_cache, new_cache)
    scopes.append({})
    res = None
    for item in iter:
        walker.assign(target, item)
        for statement in body:
            res = walker.eval_node(statement)
    scopes.pop()
    return res


async def eval_if(test_future, body, orelse, scopes, old_cache, new_cache):
    test = await test_future
    walker = Walker(scopes, old_cache, new_cache)
    scopes.append({})
    res = None
    if test:
        for statement in body:
            res = walker.eval_node(statement)
    else:
        for statement in orelse:
            res = walker.eval_node(statement)
    scopes.pop()
    return res


async def eval_ifexp(test_future, body, orelse, scopes, old_cache, new_cache):
    test = await test_future
    walker = Walker(scopes, old_cache, new_cache)
    return walker.eval_node(body) if test else walker.eval_node(orelse)


async def eval_listcomp(items_future, target, elt, scopes, old_cache, new_cache):
    items = await resolve(items_future)
    walker = Walker(scopes, old_cache, new_cache)
    res = []
    scopes.append({})
    for item in items:
        walker.assign(target, item)
        res.append(walker.eval_node(elt))
    scopes.pop()
    return res
