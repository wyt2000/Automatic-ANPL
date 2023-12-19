from . import eval_program
from . import get_sorted_funcs
from ..Tracer import IOCollector

from typing import Any, Dict, List, Tuple

__all__ = ['trace_code']

def trace_code(code: str,
               inputs: List[Any] | str,
               entry_name: str = 'main') -> Tuple[List[str], Dict[str, str], IOCollector, Exception]:
    # Get function names and codes
    try:
        func_names_sorted, func_codes = get_sorted_funcs(code)
    except Exception as e:
        return None, None, None, Exception(f"{e}: {code.splitlines()[e.lineno - 1].strip()}")

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