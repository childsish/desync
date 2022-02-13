import ast
import inspect

from swee.hashtools import hash_function
from typing import Callable


class Function:
    def __init__(self, func: Callable):
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    @property
    def name(self):
        return self._func.__name__

    def get_ast(self):
        return ast.parse(inspect.getsource(self._func))

    def get_signature(self):
        return inspect.signature(self._func)

    def get_source(self):
        return inspect.getsource(self._func)

    def get_module(self):
        return inspect.getmodule(self._func)

    def get_hash(self) -> int:
        return hash_function(self._func)

    def get_step_hashes(self):
        module = self.get_ast()

        step_hashes = []
        stack = module.body[:]
        while len(stack) > 0:
            top = stack.pop(0)
            if isinstance(top, (ast.Assign, ast.Return)):
                stack.append(top.value)
            elif isinstance(top, ast.Attribute):
                stack.append(top.value)
            elif isinstance(top, ast.FunctionDef):
                stack.extend(top.body)
            elif isinstance(top, ast.ListComp):
                stack.append(top.elt)
            elif isinstance(top, ast.Call) and hasattr(top.func, 'id'):
                func = inspect.getmodule(self._func).__dict__[top.func.id]
                if type(func).__name__ == 'Desync':
                    step_hashes.extend(func.get_version().minor_hash)
                elif not inspect.isbuiltin(func):
                    step_hashes.append(hash_function(func))
        return tuple(sorted(step_hashes))
