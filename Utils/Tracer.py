import functools
import traceback
import functools
from .ProgramOperations.get_sorted_funcs import get_sorted_funcs
import timeout_decorator
from copy import deepcopy
from types import FunctionType, ModuleType
from typing import Any, List, Dict, Tuple

from .ProgramOperations import eval_program

__all__ = [
    'IOExample',
    'IOCollector',
    'trace_code',
]

class TraceException(Exception):
    # Exception with lineno in str module.
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
    # input-output pair with exception for function.
    def __init__(self,
                 inp: Dict[str, str],
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
    # Wrap func in module to record input/output when exec.
    def __init__(self,
                 code: str, # for lineno -> line str
                 func_names: List[str],
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

    @staticmethod
    def get_lineno_for_function(code: List[str], func_name: str):
        # Get func lineno from code_str
        for i, line in enumerate(code):
            if f'def {func_name}' in line:
                return i + 1
        return -1

    def set_trace(self, func: FunctionType):
        # Wrap function to save I/O in func_ios when execuated

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
                    lineno = self.get_lineno_for_function(self.full_code, func_name)
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

def trace_code(code: str,
               inputs: List[Any] | str,
               entry_name: str = 'main') -> Tuple[List[str], Dict[str, str], IOCollector, Exception]:
    # Get function names and codes
    try:
        func_names_sorted, func_codes = get_sorted_funcs(code)
    except Exception as e:
        te = traceback.TracebackException.from_exception(e)
        lineno = te.stack[0].lineno
        return None, None, None, Exception(f"{e}: {code.splitlines()[lineno - 1].strip()}") 

    # Trace all functions in code
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
