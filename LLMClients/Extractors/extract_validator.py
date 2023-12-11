import ast

__all__ = ['extract_validator']

def extract_validator(code: str):
    # Remove all statement except function define in the top module to avoid exception
    try:
        root = ast.parse(code)
        root.body = [node for node in root.body if isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
        code = ast.unparse(root)
    except Exception as err:
        return None
    return code
