from functools import partial

import Prompts.ProgramPrompts as Prompts
from ..Clients import LLMClient 
from Utils.FileOperations import save_all
from Utils.ProgramOperations import inject_func_to_class

__all__ = ['GenerateSolution']

@inject_func_to_class(LLMClient)
async def GenerateSolution(client: LLMClient,
                                task_name: str,
                                question: str,
                                save_dir: str,
                                completion_kwargs: dict,
                                num_completions: int):
    # Request from chatGPT to get high-level solution for question.

    return await client.request(
        task_name               = task_name,
        task_kind               = 'solution',
        prompt_template         = Prompts.GenerateSolution,
        prompt_kwargs           = {'question' : question},
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.plan'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions 
    )
