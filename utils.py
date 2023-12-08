import ast
from typing import Any

from Tracer import eval_program
from Configs import CONFIG
from Utils.ProgramOperations.remove_implemented_functions import remove_implemented_functions

# Extract import lines of ANPL or Python codes
def extract_imports(code: str):
    return '\n'.join([line for line in code.splitlines() if line.startswith('import ') or line.startswith('from ')])

# Extract vaild Python code or ANPL code
def extract_code(content: str):
    if not '`' in content:
        return content
    code = []
    is_target = False
    for line in content.splitlines():
        if '`' in line:
            if is_target:
                break
            else:
                is_target = True
                continue
        if is_target:
            code.append(line)
    return '\n'.join(code)

# Extract anpl code and add imports from question 
def extract_anpl(content: str, question: str):
    return '\n'.join([extract_imports(question), content])

# Filter other functions, but allow decompose
def extract_func(content: str, target: str, func_names: set[str]):
    return remove_implemented_functions(content, target, func_names - {target})

#############################################################################
# Extract assert statements
class AssertVisitor(ast.NodeVisitor):
    def __init__(self):
        self.asserts = set()

    def visit_Assert(self, node):
        self.asserts.add(ast.unparse(node))

def extract_asserts(content: str):
    asserts = set()
    try:
        root = ast.parse(content)
        visitor = AssertVisitor()
        visitor.visit(root)
        asserts = visitor.asserts
    except Exception:
        pass
    return '\n'.join(asserts)
#############################################################################

# Check if the code is valid Python code with function `entry_point`.
def verify_anpl(code: str, entry_point: str) -> bool:
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

# Remove implementations of non-entry functions.
def collect_anpl(code: str, entry_point: str) -> str:
    root = ast.parse(code)
    for node in root.body:
        if isinstance(node, ast.FunctionDef) and node.name != entry_point:
            docstring = ast.get_docstring(node)
            node.body = [ast.Expr(ast.Str(docstring))]
    return ast.unparse(root)

# Merge entry function with asserts to anpl code.
def collect_anpl_with_asserts(entry_func: str, anpl_code: str, entry_point: str) -> str:
    try:
        root = ast.parse(anpl_code)
        root.body = [node for node in root.body if not (isinstance(node, ast.FunctionDef) and node.name == entry_point)]
        anpl_code = '\n'.join([ast.unparse(root), entry_func])
    except Exception:
        pass
    return anpl_code 

# Verify python syntax, faster than `ast.parse`.
def verify_python(string):
    if not string: return False
    try:
        compile(string, '<string>', 'exec')
        return True
    except SyntaxError:
        return False

#############################################################################
# TODO: support APPS
# Find the assert which makes the program fail
def collect_counterexample(asserts: list[str], program: str, entry_point: str) -> str:
    for assert_stmt in asserts:
        try:
            _, exc = eval_program(
                code       = program,
                entry_name = entry_point,
                inputs     = assert_stmt
            ) 
        except Exception as err:
            exc = err
        if exc is not None:
            return assert_stmt 
    return None

# Check if the program will raise an exception when tested by asserts
def verify_counterexample(asserts: str, program: str, entry_point: str) -> bool:
    return collect_counterexample(asserts.splitlines(), program, entry_point) is not None

def collect_counterexample_with_validator(code: str, entry_point: str, validators: list[str], test_inputs: list[list[Any]]) -> list[str, list[Any]]:
    for validator in validators:
        code_with_validator = '\n'.join([code, validator])
        for inputs in test_inputs:
            try:
                _, exc = eval_program(
                    code       = code_with_validator,
                    entry_name = f'validate_{entry_point}',
                    inputs     = inputs 
                ) 
            except Exception as err:
                exc = err
            if exc is not None:
                return validator, inputs
    return None, None 

#############################################################################


#############################################################################
class AssertToPassVisitor(ast.NodeTransformer):
    # Convert all assert and raise statements to `pass`.
    def visit_Assert(self, node):
        return ast.Pass()
    def visit_Raise(self, node):
        return ast.Pass()

def prepare_for_submit(code: str):
    # Transform the code before submit
    try:
        root = ast.parse(code)
        AssertToPassVisitor().visit(root)
        code = ast.unparse(root)
        code = '\n'.join(['from typing import *\n', code])
    except Exception:
        pass
    return code
#############################################################################

#############################################################################
# Check if the code has a callable input generator `func_name`.
def verify_input_generator(code: str, func_name: str) -> bool:
    _, exc = eval_program(code, func_name, [CONFIG.seed])
    if exc:
        return False
    return True

# Generate random inputs by input generator `func_name`.
def collect_random_input(funcs: list[str], func_name: str, num_random_inputs: int) -> list[list[Any]]:
    random_inputs = []
    for func in funcs:
        for seed in range(CONFIG.seed, CONFIG.seed + num_random_inputs):
            try:
                ios, exc = eval_program(
                    code       = func,
                    entry_name = func_name,
                    inputs     = [seed],
                    with_trace = True,
                    func_names = [func_name]
                )
                if exc: raise exc
                random_inputs.append(ios[func_name][0].output) 
            except Exception as err:
                pass
    return random_inputs

#############################################################################
# Remove all statement except function define in the top module to avoid exception
def extract_validator(code: str):
    try:
        root = ast.parse(code)
        root.body = [node for node in root.body if isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
        code = ast.unparse(root)
    except Exception as err:
        return None
    return code
