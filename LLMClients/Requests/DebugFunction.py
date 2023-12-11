from functools import partial
from typing import Set, List

from Utils.ProgramOperations import inject_func_to_class
from Utils.Tracer import IOExample
from Utils.ProgramOperations import remove_asserts, compose_function_with_traces

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code, extract_func
from ..Verifiers import verify_python

__all__ = ['DebugFunction']

@inject_func_to_class(LLMClient)
async def DebugFunction(client: LLMClient,
                        task_name: str,
                        question: str,
                        solution: str,
                        program: str,
                        target: str,
                        func_names: Set[str],
                        func_code: str,
                        func_traces: List[IOExample],
                        completion_kwargs: dict,
                        num_completions: int):

    # Request from chatGPT to get repaired function by solution, program and traces.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'function_debug',
        prompt_template         = Prompts.DebugFunction,
        prompt_kwargs           = {'question' : question, 'solution' : solution, 'program' : program, 'function_with_traces' : compose_function_with_traces(func_code, func_traces), 'func_name' : target},
        response_handlers       = [
            extract_code,
            partial(extract_func, target=target, func_names=func_names),
            partial(remove_asserts, func_name=target)
        ],
        response_collector      = lambda res : sorted(set(filter(verify_python, res))),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
    )
