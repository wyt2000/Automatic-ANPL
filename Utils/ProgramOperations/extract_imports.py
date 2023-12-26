import ast

__all__ = ['extract_imports']

def extract_imports(code: str):
    # Extract import lines of ANPL or Python codes
    imports = ''
    try:
        root = ast.parse(code)
        root.body = [node for node in root.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        imports = ast.unparse(root)
    except Exception as err:
        pass
    return imports 

