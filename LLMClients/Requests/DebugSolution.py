from functools import partial

from Utils.ProgramOperations import inject_func_to_class
from Utils.FileOperations import save_all

from .. import Prompts
from ..Clients import LLMClient 

__all__ = ['DebugSolution']

@inject_func_to_class(LLMClient)
async def DebugSolution(client: LLMClient,
                        task_name: str,
                        question: str,
                        old_solution: str,
                        counterexample: str,
                        save_dir: str,
                        completion_kwargs: dict,
                        num_completions: int):

    # Request from chatGPT to get repaired high-level solution for question and counterexample.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'solution_debug',
        prompt_template         = Prompts.DebugSolution,
        prompt_kwargs           = {'question' : question, 'solution' : old_solution, 'counterexample' : counterexample},
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.fixed_plan'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions
    )
