import ast
import asyncio

from swee.futuretools import ensure_future, is_future
from typing import Sequence


class Walker:
    def __init__(self, scopes):
        self._scopes = scopes
        self._orphan_tasks = []

    def eval_node(self, node):
        if isinstance(node, ast.Assign):
            self.eval_assign(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Expr):
            return self.eval_expr(node)
        elif isinstance(node, ast.FunctionDef):
            return self.eval_functiondef(node)
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
        elif not isinstance(node.targets[0], (ast.Tuple, ast.List)):
            self.set_value(node.targets[0].id, ensure_future(value))
        else:
            if is_future(value):
                loop = asyncio.get_running_loop()
                futures = [loop.create_future() for _ in node.targets[0].elts]
                self._orphan_tasks.append(asyncio.create_task(eval_assign(futures, value)))
            else:
                futures = [ensure_future(subvalue) for subvalue in value]

            for target, future in zip(node.targets, futures):
                self.set_value(target.id, future)

    def eval_call(self, node: ast.Call):
        return asyncio.create_task(eval_call(
            self.eval_node(node.func),
            [self.eval_node(arg) for arg in node.args],
            [self.eval_node(keyword) for keyword in node.keywords],
        ))

    def eval_expr(self, node: ast.Expr):
        return self.eval_node(node.value)

    def eval_functiondef(self, node: ast.FunctionDef):
        res = None
        for statement in node.body:
            res = self.eval_node(statement)
        return res

    def eval_name(self, node: ast.Name):
        for scope in self._scopes[::-1]:
            if node.id in scope:
                return scope[node.id]
        return getattr(__builtins__, node.id)

    def eval_return(self, node: ast.Return):
        return self.eval_node(node.value)

    def copy_scopes(self):
        return [scope for scope in self._scopes]

    def get_value(self, key):
        return self._scopes[-1][key]

    def set_value(self, key, value):
        self._scopes[-1][key] = value


async def eval_assign(futures: Sequence[asyncio.Future], value):
    await value
    for future, sub_value in zip(futures, value.result()):
        future.set_result()


async def eval_call(func, pre_args, pre_kwargs):
    await asyncio.gather(*pre_args)
    await asyncio.gather(*pre_kwargs)
    args = [arg.result() for arg in pre_args]
    kwargs = {key: value.result() for key, value in pre_kwargs}
    return func(*args, **kwargs)
