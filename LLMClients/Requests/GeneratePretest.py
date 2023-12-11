from functools import partial

import Prompts.ProgramPrompts as Prompts
from ..Clients import LLMClient 
from Utils.FileOperations import save_one
from Utils.ProgramOperations import inject_func_to_class
from ..Extractors import extract_code, extract_asserts

__all__ = ['GeneratePretest']

@inject_func_to_class(LLMClient)
async def GeneratePretest(client: LLMClient,
                          task_name: str,
                          question: str,
                          save_dir: str,
                          completion_kwargs: dict,
                          num_completions: int,
                          retry_times: int = 5):
    # Request from chatGPT to get pretests for question.

    return await client.request(
        task_name               = task_name,
        task_kind               = 'pretest',
        prompt_template         = Prompts.GeneratePretest,
        prompt_kwargs           = {'question' : question},
        response_handlers       = [extract_code, extract_asserts],
        response_verifier       = lambda assert_str : len(assert_str) > 0,
        response_collector      = lambda res : '\n'.join(sorted(set(stmt for r in res for stmt in r.splitlines()))),
        response_saver          = partial(save_one, save_dir=save_dir, filename=f'{task_name}.test'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
        retry_times             = retry_times
    )

