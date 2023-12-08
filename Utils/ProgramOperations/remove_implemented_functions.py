import ast
from typing import Set

__all__ = ['remove_implemented_functions']

class FuncDefTransformer(ast.NodeTransformer):
    def __init__(self, removed_funcs: Set[str]):
        self.removed_funcs = removed_funcs 

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if node.name in self.removed_funcs:
            return None
        return node

def remove_implemented_functions(raw_code: str, target: str, implemented_functions: Set[str]):
    # Remove all implemented functions including nested functions
    code = None
    try:
        root = ast.parse(raw_code)
        if not any(node.name == target for node in root.body if isinstance(node, ast.FunctionDef)):
            return None
        visitor = FuncDefTransformer(implemented_functions)
        visitor.visit(root)
        code = ast.unparse(root)
    except Exception:
        pass
    return code