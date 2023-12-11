
__all__ = ['extract_imports']

# TODO: use AST
def extract_imports(code: str):
    # Extract import lines of ANPL or Python codes
    return '\n'.join([line for line in code.splitlines() if line.startswith('import ') or line.startswith('from ')])
