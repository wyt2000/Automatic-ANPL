import ast
import traceback

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
    def __init__(self):
        self.func_names = []
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.func_names.append(node.name)
        self.generic_visit(node)
        self.func_names.pop()
        return node
    def visit_Assert(self, node: ast.Assert):
        if not self.func_names:
            return ast.Pass()
        visitor = AssertNameVisitor(self.func_names[-1])
        visitor.visit(node)
        if visitor.has_target:
            return ast.Pass()
        return node

def remove_asserts(content: str):
    # Remove the asserts outside of all functions and the recursive call in asserts 
    try:
        root = ast.parse(content)
        AssertRemover().visit(root)
        content = ast.unparse(root)
    except Exception as err:
        pass
    return content