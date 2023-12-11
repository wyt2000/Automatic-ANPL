from functools import partial
from typing import Set

from Utils.ProgramOperations import inject_func_to_class
from Utils.ProgramOperations import remove_asserts

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code, extract_func
from ..Verifiers import verify_python

__all__ = ['GenerateFunction']

@inject_func_to_class(LLMClient)
async def GenerateFunction(client: LLMClient,
                           task_name: str,
                           prefix: str,
                           code: str,
                           hole: str,
                           target: str,
                           func_names: Set[str],
                           use_asserts: bool,
                           completion_kwargs: dict,
                           num_completions: int):
                           
    # Request from chatGPT to get function completions from hole.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'function_completion',
        prompt_template         = Prompts.GenerateFunctionWithAsserts if use_asserts else Prompts.GenerateFunctionWithAsserts,
        prompt_kwargs           = {'prefix' : prefix, 'code' : code, 'hole' : hole, 'func_name' : target},
        response_handlers       = [
            extract_code,
            partial(extract_func, target=target, func_names=func_names),
            partial(remove_asserts, func_name=target)
        ],
        response_collector      = lambda res : sorted(set(filter(verify_python, res))),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
    )
