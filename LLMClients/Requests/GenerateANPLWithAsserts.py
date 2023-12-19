from functools import partial
from typing import Set

from Utils.ProgramOperations import inject_func_to_class, remove_asserts 
from Utils.FileOperations import save_all 
from Configs import CONFIG

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code, extract_func
from ..Verifiers import verify_python
from ..Collectors import collect_anpl_with_asserts

__all__ = ['GenerateANPLWithAsserts']

@inject_func_to_class(LLMClient)
async def GenerateANPLWithAsserts(client: LLMClient,
                                  task_name: str,
                                  question: str,
                                  solution: str,
                                  anpl_code: str,
                                  entry_point: str,
                                  func_code: str,
                                  func_names: Set[str],
                                  save_dir: str,
                                  completion_kwargs: dict,
                                  num_completions: int,
                                  retry_times: int = CONFIG.verifier_retry_times):

    # Request from chatGPT to add assertions for the function.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'assertion',
        prompt_template         = Prompts.GenerateANPLWithAsserts,
        prompt_kwargs           = {'question' : question, 'solution' : solution, 'program' : anpl_code, 'function' : func_code, 'func_name' : entry_point},
        response_handlers       = [
            extract_code,
            partial(extract_func, target=entry_point, func_names=func_names),
            remove_asserts
        ],
        response_verifier       = verify_python,
        response_collector      = lambda res : list(map(partial(collect_anpl_with_asserts, anpl_code=anpl_code, entry_point=entry_point), res)),
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.anpl_with_asserts'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
        retry_times             = retry_times
    )
