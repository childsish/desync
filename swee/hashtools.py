import ast
import inspect
import zlib


def hash_function(func):
    tree = ast.parse(inspect.getsource(func))
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef)
    tree.body[0].name = ''
    for node in ast.walk(tree):
        remove_docstring(node)
    ast_str = ast.dump(tree, annotate_fields=False)
    return zlib.adler32(ast_str.encode('ascii'))


def hash_input(args, kwargs):
    hash_ = zlib.adler32(str(args).encode('ascii'))
    return zlib.adler32(str(sorted(kwargs.items())).encode('ascii'), hash_)


def remove_docstring(node: ast.AST):
    if not (isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef)):
        return
    if len(node.body) != 0:
        docstr = node.body[0]
        if isinstance(docstr, ast.Expr) and isinstance(docstr.value, ast.Str):
            node.body.pop(0)
