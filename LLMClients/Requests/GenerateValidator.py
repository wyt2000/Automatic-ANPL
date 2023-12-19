from functools import partial

from Utils.ProgramOperations import inject_func_to_class
from Utils.FileOperations import save_all
from Configs import CONFIG

from .. import Prompts
from ..Clients import LLMClient 
from ..Extractors import extract_code, extract_validator
from ..Verifiers import verify_python 

__all__ = ['GenerateValidator']

@inject_func_to_class(LLMClient)
async def GenerateValidator(client: LLMClient,
                            task_name: str,
                            func_name: str,
                            func_code: str,
                            save_dir: str,
                            completion_kwargs: dict,
                            num_completions: int,
                            retry_times: int = CONFIG.verifier_retry_times):

    # Request from chatGPT to validate the function.
    return await client.request(
        task_name               = task_name,
        task_kind               = 'validator',
        prompt_template         = Prompts.GenerateValidator,
        prompt_kwargs           = {'func_name': func_name, 'function': func_code},
        response_handlers       = [extract_code, extract_validator],
        response_verifier       = verify_python,
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.validator'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions,
        retry_times             = retry_times
    )
