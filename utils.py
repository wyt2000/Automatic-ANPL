import os
import shutil
import pathlib
import coloredlogs
import importlib
import logging 
import logging.config
import json
import functools
import operator
import random
import re
import ast
from contextlib import contextmanager, redirect_stdout
from Tracer import eval_program, IOExample

def mkdir_override(dir_path):
    '''
    mkdir: override if exists.
    '''
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    pathlib.Path(dir_path).mkdir(parents=True)

def mkdir_no_override(dir_path):
    '''
    mkdir: do nothing if exists.
    '''
    if os.path.exists(dir_path):
        return
    pathlib.Path(dir_path).mkdir(parents=True)

color_ansi = {
    'red'   : '\033[31m',
    'green' : '\033[32m',
    'reset' : '\033[00m'
}
def color_str(s, color):
    '''
    Add color to str. 
    '''
    if color not in color_ansi:
        return s
    return color_ansi[color] + s + color_ansi['reset']

class ColoredFormatter(coloredlogs.ColoredFormatter):
    '''
    Colored log formatter.
    '''
    def __init__(self, fmt=None, datefmt=None, style='%'):
        '''Match coloredlogs.ColoredFormatter arguments with logging.Formatter'''
        coloredlogs.ColoredFormatter.__init__(self, fmt=fmt, datefmt=datefmt)

def make_object(module_name, class_name, **kwargs):
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls(**kwargs)

@contextmanager
def redirect_loggers(log_path: str):
    '''
    Redirect loggers output to file
    '''
    file_handler = logging.FileHandler(log_path)
    root_logger = logging.getLogger('root')
    root_handlers = [root_logger.handlers[0]]
    root_logger.handlers = [file_handler]
    try:
        yield 
    finally:
        file_handler.close()
        root_logger.handlers = root_handlers

def product_to_tensor_idx(prod, dims, idx):
    ans = []
    for dim in dims:
        prod //= dim
        ans.append(idx // prod)
        idx %= prod
    return ans

def sample_product(arrs, n, k):
    indices = random.sample(range(n), k)
    dims = [len(arr) for arr in arrs]
    prod = functools.reduce(operator.mul, dims, 1)
    return [
        product_to_tensor_idx(prod, dims, idx)
        for idx in indices
    ]

# Remove all implemented functions including nested functions
func_pattern = re.compile(r"\s*def\s+(.+)\(.*\).*\:")
def remove_implemented_functions(raw_code: str, target: str, implemented_functions: set[str]):
    # When meet the line "def {implemented_functions}", omit lines until the line whose indent count <= its
    has_target = False
    is_omit = False
    omit_indent = -1
    code = []
    for line in raw_code.splitlines():
        indent = len(line) - len(line.lstrip())
        if is_omit: # in scope of implemented functions
            if indent > omit_indent: continue
            is_omit = False
        if m := func_pattern.match(line): # meet func def
            func_name = m.group(1)
            if indent == 0 and func_name == target:
                has_target = True
            if func_name in implemented_functions: 
                is_omit = True
                omit_indent = indent
                continue
        code.append(line)
    return '\n'.join(code) if has_target else None

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

# Filter other functions, but allow decompose
def extract_func(content: str, target: str, func_names: set[str]):
    return remove_implemented_functions(content, target, func_names - {target})

class AssertVisitor(ast.NodeVisitor):
    def __init__(self):
        self.asserts = set()

    def visit_Assert(self, node):
        self.asserts.add(ast.unparse(node))

# Extract assert statements
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

# Check if the code is valid Python code with function `entry_point`.
def verify_anpl(code: str, entry_point: str) -> bool:
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

# Verify python syntax, faster than `ast.parse`.
def verify_python(string):
    if string is None: return False
    try:
        compile(string, '<string>', 'exec')
        return True
    except SyntaxError:
        return False

# TODO: support APPS
# Find the assert which makes the program fail
def collect_counterexample(asserts: str, program: str, entry_point: str) -> str:
    for assert_stmt in asserts.splitlines():
        try:
            _, exc = eval_program(program, entry_point, assert_stmt) 
        except Exception as err:
            exc = err
        if exc is not None:
            return assert_stmt 
    return None

# Check if the program will raise an exception when tested by asserts
def verify_counterexample(asserts: str, program: str, entry_point: str) -> bool:
    return collect_counterexample(asserts, program, entry_point) is not None

# Add trace before function code
def compose_function_with_traces(func_code: str, func_traces: list[IOExample]) -> str:
    function_with_traces = "# Trace: \n"
    for trace in func_traces:
        function_with_traces += f"# {repr(trace)}\n"
    function_with_traces += func_code
    return function_with_traces
