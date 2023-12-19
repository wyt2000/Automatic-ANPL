import ast

__all__ = ['prepare_for_submit']

class AssertToPassVisitor(ast.NodeTransformer):
    # Convert all assert and raise statements to `pass`.
    def visit_Assert(self, node):
        return ast.Pass()
    def visit_Raise(self, node):
        return ast.Pass()

def prepare_for_submit(code: str):
    # Transform the code before submit
    try:
        root = ast.parse(code)
        AssertToPassVisitor().visit(root)
        code = ast.unparse(root)
        code = '\n'.join(['from typing import *\n', code])
    except Exception:
        pass
    return code
