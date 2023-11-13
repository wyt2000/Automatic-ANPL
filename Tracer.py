import functools
import traceback
import sys
import importlib.util
import functools
import timeout_decorator
from copy import deepcopy
from types import FunctionType, ModuleType
import io as IO
from contextlib import redirect_stdout
import resource
import code
import ast
from typing import Any

# Import program str as module.
def import_module_from_string(source: str):
    spec = importlib.util.spec_from_loader("test", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(source, module.__dict__)
    return module

# Get func lineno from code_str
def get_lineno_for_function(code: list[str], func_name: str):
    for i, line in enumerate(code):
        if f'def {func_name}' in line:
            return i + 1
    return -1

class TraceException(Exception):
    '''
    Exception with lineno in str module.
    '''
    def __init__(self,
                 lineno: int,
                 func_name: str,
                 code: str,
                 *args):
        super().__init__(*args)
        self.lineno = lineno
        self.func_name = func_name
        self.code = code

    def __repr__(self):
        return f"{super().args[0].__repr__()} at line {self.lineno} in function \'{self.func_name}\': {self.code.strip()}"

class IOExample:
    '''
    input-output pair with exception for function.
    '''
    def __init__(self,
                 inp: dict[str, str],
                 out: str,
                 exc: Exception = None):
        self.input     = inp
        self.output    = out
        self.exception = exc 

    def __repr__(self):
        if self.exception is None:
            return f'input: {repr(self.input)}, output: {repr(self.output)}'
        return f'input: {repr(self.input)}, exception: {repr(self.exception)}'

class IOCollector:
    '''
    Wrap func in module to record input/output when exec.
    '''
    def __init__(self,
                 code: str, # for lineno -> line str
                 func_names: list[str],
                 module: ModuleType,
                 limit: int= 3):

        self.full_code  = code.splitlines()
        self.func_names = func_names
        self.func_ios   = {}
        self.limit      = limit

        # Trace all functions in func_names
        for name in func_names:
            func = getattr(module, name, None)
            if func and isinstance(func, FunctionType):
                setattr(module, name, self.set_trace(func))
    
    def __repr__(self):
        return f"IOCollector({self.func_ios})"

    def __getitem__(self, key):
        return self.func_ios.get(key, [])

    # Wrap function to save I/O in func_ios when execuated
    def set_trace(self, func: FunctionType):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # Get formal args and actual args
            names, values = func.__code__.co_varnames[:func.__code__.co_argcount], args
            inputs = {name: value for name, value in zip(names, values)}
            if kwargs:
                inputs = inputs | kwargs

            # Exec functions and copy ios or exception
            frozen_inputs = deepcopy(inputs)
            output = None
            exc = None
            try:
                output = func(*args, **kwargs)
            except Exception as e:
                te = traceback.TracebackException.from_exception(e)
                if isinstance(e, TraceException):
                    # skip wrapper function
                    te.stack.pop() 
                    e = e.args[0]
                elif isinstance(e, timeout_decorator.TimeoutError): 
                    # skip call stack in timeout decorator  
                    while te.stack and te.stack[-1].name != func.__name__:
                        te.stack.pop()
                lineno = te.stack[-1].lineno if te.stack else -1
                func_name = te.stack[-1].name if te.stack else ""
                if not func_name or func_name == 'wrapper': 
                    # Handle exception before entering func, eg: arg number not match 
                    func_name = func.__name__
                    lineno = get_lineno_for_function(self.full_code, func_name)
                code = self.full_code[lineno - 1] if 0 <= lineno - 1 < len(self.full_code) else ""
                exc = TraceException(lineno, func_name, code, e)
            frozen_output = deepcopy(output)

            # Save trace as IOExample
            func_name = func.__name__
            if func_name not in self.func_ios:
                self.func_ios[func_name] = []
            if len(self.func_ios[func_name]) < self.limit:
                self.func_ios[func_name].append(IOExample(frozen_inputs, frozen_output, exc))

            # Handle nested exception
            if exc:
                raise exc

            return output
        return wrapper

# Run code and save traces of func_names (optional), NOT support kwargs 
@timeout_decorator.timeout(1)
def eval_program(code: str,
                 entry_name: str,
                 inputs: list[Any] | str,
                 with_trace: bool = False,
                 func_names: list[str] = None,
                 ) -> list[IOCollector | None, Exception]:
    io, exc = None, None

    # Save resource usage limit
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    recursion_limit = sys.getrecursionlimit()
    try:
        with redirect_stdout(IO.StringIO()):
            # Limit resource usage
            resource.setrlimit(resource.RLIMIT_AS, (1 << 32, hard))
            sys.setrecursionlimit(100)

            # Load module from code and find entry function
            module = import_module_from_string(code)
            if with_trace: io = IOCollector(code, func_names, module)
            entry_func = getattr(module, entry_name, None)
            if not (entry_func and isinstance(entry_func, FunctionType)):
                raise ValueError(f"Couldn't find entry function {entry_name}")

            # Exec entry_func with inputs
            if isinstance(inputs, list):
                entry_func(*inputs) # For list[args]
            elif isinstance(inputs, str):
                exec(inputs, locals() | {entry_func.__name__: entry_func}) # For assert str
            else:
                raise TypeError("Inputs should be either list or assert str!")

    # Collect Exceptions and Recover the resource limits
    except AssertionError as err:
        exc = AssertionError(inputs) # Save assert str in Exception
    except Exception as err:
        exc = err 
    finally:
        sys.setrecursionlimit(recursion_limit)
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
    return io, exc 

# Get function names and codes in definition order of the program.
def get_sorted_funcs(program: str) -> tuple[list[str], dict[str, str]]:
    func_names_sorted = []
    func_codes = {} 
    root = ast.parse(program)
    for node in root.body:
        if isinstance(node, ast.FunctionDef):
            func: ast.FunctionDef = node
            func_names_sorted.append(func.name)
            func_codes[func.name] = ast.unparse(func)
    return func_names_sorted, func_codes

# Trace all functions in code
def trace_code(code: str,
               inputs: list[Any] | str,
               entry_name: str = 'main') -> list[dict[str, str], IOCollector, Exception]:
    # Get function names and codes
    try:
        func_names_sorted, func_codes = get_sorted_funcs(code)
    except Exception as e:
        te = traceback.TracebackException.from_exception(e)
        lineno = te.stack[0].lineno
        return None, None, None, Exception(f"{e}: {code.splitlines()[e.lineno - 1].strip()}") 

    try:
        ios, exc = eval_program(
            code        = code,
            entry_name  = entry_name,
            inputs      = inputs,
            with_trace  = True,
            func_names  = list(func_codes.keys())
        )
        return func_names_sorted, func_codes, ios, exc
    except Exception as exc:
        return func_names_sorted, func_codes, None, exc


