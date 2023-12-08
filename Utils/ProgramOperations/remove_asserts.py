import ast

__all__ = ['remove_asserts']

class AssertNameVisitor(ast.NodeVisitor):
    def __init__(self, target: str):
        self.target = target
        self.has_target = False
    def visit_Name(self, node: ast.Name):
        self.generic_visit(node)
        if node.id == self.target:
            self.has_target = True

class AssertRemover(ast.NodeTransformer):
    def __init__(self, target: str):
        self.target = target
    def visit_Assert(self, node):
        visitor = AssertNameVisitor(self.target)
        visitor.visit(node)
        if visitor.has_target:
            return None
        return node

def remove_asserts(content: str, func_name: str):
    # Remove the asserts outside of all functions and the recursive call in asserts 
    try:
        root = ast.parse(content)
        root.body = [node for node in root.body if not isinstance(node, ast.Assert)]
        AssertRemover(func_name).visit(root)
        content = ast.unparse(root)
    except Exception:
        pass
    return content