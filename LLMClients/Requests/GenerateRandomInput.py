from functools import partial

from Utils.ProgramOperations import inject_func_to_class
from Utils.FileOperations import save_one
from Configs import CONFIG

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code
from ..Verifiers import verify_input_generator
from ..Collectors import collect_random_input

__all__ = ['GenerateRandomInput']

@inject_func_to_class(LLMClient)
async def GenerateRandomInput(client: LLMClient,
                              task_name: str,
                              func_name: str,
                              func_code: str,
                              constraint: str,
                              num_random_inputs: int,
                              save_dir: str,
                              completion_kwargs: dict,
                              num_completions: int,
                              retry_times: int = CONFIG.verifier_retry_times):

    # Request from chatGPT to generate random inputs.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'random_input',
        prompt_template         = Prompts.GenerateRandomInput,
        prompt_kwargs           = {'func_name': func_name, 'function': func_code, 'constraint': constraint},
        response_handlers       = [extract_code],
        response_verifier       = partial(verify_input_generator, func_name=f'test_{func_name}'),
        response_collector      = partial(collect_random_input, func_name=f'test_{func_name}', num_random_inputs=num_random_inputs),
        response_saver          = partial(save_one, save_dir=save_dir, filename=f'{task_name}.random_input'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
        retry_times             = retry_times
    )
