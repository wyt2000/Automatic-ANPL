import openai
import logging 
import logging.config
import aiohttp
import pathlib
import json
import asyncio
from PromptBuilder.PromptBuilder import AbstractPromptBuilder

class GPTClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def delayed_completion(self, delay_in_seconds, **kwargs):
        await asyncio.sleep(delay_in_seconds)
        response = await openai.ChatCompletion.acreate(**kwargs)
        return response

    async def request(self, task_name, model_name, question, starter_code, prompt_builder: AbstractPromptBuilder, save_dir=None, delay_in_seconds=1.0):
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            # Solution Stage
            messages = prompt_builder.build_background()
            messages = prompt_builder.build_solution_request(question, messages)
            self.logger.debug(f'{task_name}: Requesting for high-level solution from {model_name}...')
            response = await self.delayed_completion(
                    delay_in_seconds = delay_in_seconds,
                    model            = model_name,
                    messages         = messages,
                    temperature      = 0.6
            )
            solution_plan = prompt_builder.get_response(response, messages)
            if save_dir is not None:
                with open(pathlib.Path(save_dir, f'{task_name}.plan'), 'w') as f:
                    f.write(solution_plan)
            self.logger.debug(f'{task_name}: Requesting for high-level solution done!')
            # Translation Stage
            messages = prompt_builder.build_translation_request(solution_plan, starter_code, messages)
            self.logger.debug(f'{task_name}: Requesting for code from {model_name}...')
            response = await self.delayed_completion(
                    delay_in_seconds = delay_in_seconds,
                    model            = model_name,
                    messages         = messages,
                    temperature      = 0.2,
                    presence_penalty = 0.1,
                    logit_bias       = {755:-100} # ban `def` to avoid generate python code
            )
            code = prompt_builder.get_response(response, messages)
            code = prompt_builder.extract_code(code)
            self.logger.debug(f'{task_name}: Requesting for code done!')
            if save_dir is not None:
                with open(pathlib.Path(save_dir, f'{task_name}.ss'), 'w') as f:
                    f.write(code)
            return code

