from functools import partial

from Utils.ProgramOperations import inject_func_to_class
from Utils.FileOperations import save_all

from .. import Prompts
from ..Clients import LLMClient 

__all__ = ['GenerateConstraint']

@inject_func_to_class(LLMClient)
async def GenerateConstraint(client: LLMClient,
                             task_name: str,
                             function: str,
                             io_type: str,
                             save_dir: str,
                             completion_kwargs: dict,
                             num_completions: int):

    # Request from chatGPT to get the input or output constraints.
    return await client._request(
        task_name               = task_name,
        task_kind               = f'{io_type}_constraint',
        prompt_template         = Prompts.GenerateConstraint,
        prompt_kwargs           = {'function' : function, 'io_type' : io_type},
        response_saver          = partial(save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.{io_type}_constraint'),
        completion_kwargs       = completion_kwargs,
        num_completions         = num_completions 
    )
