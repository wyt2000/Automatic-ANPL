import ast

__all__ = ['extract_asserts']

class AssertVisitor(ast.NodeVisitor):
    def __init__(self):
        self.asserts = set()

    def visit_Assert(self, node):
        self.asserts.add(ast.unparse(node))

def extract_asserts(content: str):
    # Extract assert statements
    asserts = set()
    try:
        root = ast.parse(content)
        visitor = AssertVisitor()
        visitor.visit(root)
        asserts = visitor.asserts
    except Exception:
        pass
    return '\n'.join(asserts)
