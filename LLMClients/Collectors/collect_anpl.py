import ast

__all__ = ['collect_anpl', 'collect_anpl_with_asserts']

def collect_anpl(code: str, entry_point: str) -> str:
    # Remove implementations of non-entry functions.
    root = ast.parse(code)
    for node in root.body:
        if isinstance(node, ast.FunctionDef) and node.name != entry_point:
            docstring = ast.get_docstring(node)
            node.body = [ast.Expr(ast.Str(docstring))]
    return ast.unparse(root)

def collect_anpl_with_asserts(entry_func: str, anpl_code: str, entry_point: str) -> str:
    # Merge entry function with asserts to anpl code.
    try:
        root = ast.parse(anpl_code)
        root.body = [node for node in root.body if not (isinstance(node, ast.FunctionDef) and node.name == entry_point)]
        anpl_code = '\n'.join([ast.unparse(root), entry_func])
    except Exception:
        pass
    return anpl_code 

