import ast
from typing import Dict, List, Tuple

__all__ = ['get_sorted_funcs']

def get_sorted_funcs(program: str) -> Tuple[List[str], Dict[str, str]]:
    # Get function names and codes in definition order of the program.
    func_names_sorted = []
    func_codes = {}
    root = ast.parse(program)
    for node in root.body:
        if isinstance(node, ast.FunctionDef):
            func: ast.FunctionDef = node
            func_names_sorted.append(func.name)
            func_codes[func.name] = ast.unparse(func)
    return func_names_sorted, func_codes