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
import asyncio
from typing import Callable, Coroutine
import time
import traceback

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

# Extract anpl code and add imports from question 
def extract_anpl(content: str, question: str):
    return '\n'.join([extract_imports(question), content])

# Filter other functions, but allow decompose
def extract_func(content: str, target: str, func_names: set[str]):
    return remove_implemented_functions(content, target, func_names - {target})

#############################################################################
# Remove the asserts outside of all functions and the recursive call in asserts 
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
    try:
        root = ast.parse(content)
        root.body = [node for node in root.body if not isinstance(node, ast.Assert)]
        AssertRemover(func_name).visit(root)
        content = ast.unparse(root)
    except Exception:
        traceback.print_exc()
        pass
    return content

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
    if string is None: return False
    try:
        compile(string, '<string>', 'exec')
        return True
    except SyntaxError:
        return False

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

# Add trace before function code
def compose_function_with_traces(func_code: str, func_traces: list[IOExample]) -> str:
    function_with_traces = "# Trace: \n"
    for trace in func_traces:
        function_with_traces += f"# {repr(trace)}\n"
    function_with_traces += func_code
    return function_with_traces

# Use with semaphone to limit active coroutine numbers
async def await_with_semaphone(async_func: Callable[[...], Coroutine], semaphone: asyncio.Semaphore, *args):
    async with semaphone:
        return await async_func(*args)

# ContextManager to record real time(ns) of the execution of a coroutine
class AsyncTimer:

    def __init__(self, start_time: int):
        self.start_time = start_time

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.time = time.time_ns() - self.start_time


