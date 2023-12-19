import ast
from Utils.ProgramOperations import eval_program

__all__ = ['verify_anpl']

def verify_anpl(code: str, entry_point: str) -> bool:
    # Check if the code is valid Python code with function `entry_point`.
    _, exc = eval_program(code, entry_point)
    if exc:
        return False
    has_entry_point = False
    try:
        root = ast.parse(code)
        for node in root.body:
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node) is None:
                    return False
                has_entry_point |= (node.name == entry_point)
    except Exception:
        return False
    return has_entry_point
