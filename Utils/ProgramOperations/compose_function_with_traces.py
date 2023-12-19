from typing import List
from ..Tracer import IOExample

__all__ = ['compose_function_with_traces']

def compose_function_with_traces(func_code: str, func_traces: List[IOExample]) -> str:
    # Add trace before function code
    function_with_traces = "# Trace: \n"
    for trace in func_traces:
        function_with_traces += f"# {repr(trace)}\n"
    function_with_traces += func_code
    return function_with_traces