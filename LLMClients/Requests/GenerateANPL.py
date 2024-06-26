from functools import partial

from Utils.ProgramOperations import inject_func_to_class
from Utils.FileOperations import save_all
from Configs import CONFIG 

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code, extract_anpl
from ..Verifiers import verify_anpl
from ..Collectors import collect_anpl

__all__ = ['GenerateANPL']

@inject_func_to_class(LLMClient)
async def GenerateANPL(client: LLMClient,
                       task_name: str,
                       entry_point: str,
                       question: str,
                       solution: str,
                       save_dir: str,
                       completion_kwargs: dict,
                       num_completions: int,
                       retry_times: int = CONFIG.verifier_retry_times):

    # Request from chatGPT to get code for high-level solution.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'translation',
        prompt_template         = Prompts.GenerateANPL,
        prompt_kwargs           = {'question' : question, 'solution' : solution, 'entry_point' : entry_point},
        response_handlers       = [extract_code, partial(extract_anpl, question=question)],
        response_verifier       = partial(verify_anpl, entry_point=entry_point),
        response_collector      = lambda res : list(map(partial(collect_anpl, entry_point=entry_point), res)),
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.anpl'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
        retry_times             = retry_times
    )
