from contextlib import redirect_stdout
import importlib.util
import timeout_decorator
import io as IO
import resource
import sys
from types import FunctionType
from typing import Any, List, Tuple

from ..Tracer import IOCollector
from Configs import CONFIG

__all__ = ['eval_program']

def import_module_from_string(source: str):
    # Import program str as module.
    spec = importlib.util.spec_from_loader("test", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(source, module.__dict__)
    return module

def eval_program(code: str,
                 entry_name: str,
                 inputs: List[Any] | str = None,
                 with_trace: bool        = False,
                 func_names: List[str]   = None,
                 timeout: float          = CONFIG.eval_program_timeout
                 ) -> Tuple[IOCollector | None, Exception]:

    # Run code and save traces of func_names (optional), NOT support kwargs 
    io, exc = None, None

    @timeout_decorator.timeout(timeout)
    def eval_program_impl():
        nonlocal io, exc
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
                if inputs is None:
                    exec(code) # for anpl syntax check
                elif isinstance(inputs, list):
                    entry_func(*inputs) # For list[args]
                elif isinstance(inputs, str):
                    exec(inputs, locals() | {entry_func.__name__: entry_func}) # For assert str
                else:
                    raise TypeError("Inputs should be either list or assert str!")
        # Collect Exceptions and Recover the resource limits
        except AssertionError as err:
            exc = err if err.args else AssertionError(inputs)
        except Exception as err:
            exc = err
        finally:
            sys.setrecursionlimit(recursion_limit)
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))

    eval_program_impl()
    return io, exc

