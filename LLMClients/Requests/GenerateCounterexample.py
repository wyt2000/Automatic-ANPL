from functools import partial

from Utils.ProgramOperations import inject_func_to_class
from Utils.FileOperations import save_all

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code, extract_asserts
from ..Verifiers import verify_counterexample
from ..Collectors import collect_counterexample

__all__ = ['GenerateCounterexample']

@inject_func_to_class(LLMClient)
async def GenerateCounterexample(client: LLMClient,
                                 task_name: str,
                                 question: str,
                                 program: str,
                                 entry_point: str,
                                 save_dir: str,
                                 completion_kwargs: dict,
                                 num_completions: int,
                                 retry_times: int = 5):

    # Request from chatGPT to get counterexamples of the program.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'counterexamples',
        prompt_template         = Prompts.GenerateCounterexample,
        prompt_kwargs           = {'question' : question, 'program' : program},
        response_handlers       = [extract_code, extract_asserts],
        response_verifier       = partial(verify_counterexample, program=program, entry_point=entry_point),
        response_collector      = lambda res : list(map(partial(collect_counterexample, program=program, entry_point=entry_point), res)),
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.counterexample'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
        retry_times             = retry_times
    )
