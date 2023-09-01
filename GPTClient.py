import openai
import logging 
import logging.config
import aiohttp
import pathlib
import json
import asyncio
import re
from Prompter.Prompter import AbstractPrompter

class GPTClient:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern = re.compile("^\s*[^\d\W]\w*\(.*\).*\:")

    async def delayed_completion(self, delay_in_seconds, **kwargs):
        '''
        Delay `delay_in_seconds`, then async call `ChatCompletion`.
        '''
        await asyncio.sleep(delay_in_seconds)
        response = await openai.ChatCompletion.acreate(**kwargs)
        return response

    def get_response_list(self, responses):
        '''
        Convert GPT responses to list[str]
        '''
        return [response["message"]["content"] for response in responses["choices"]]

    def extract_code(self, response):
        code = response.split('\n')
        code = '\n'.join([line for line in code if self.pattern.match(line)])
        return code

    async def request_for_solutions(self,
                                    task_name: str,
                                    question: str,
                                    prompter: AbstractPrompter,
                                    save_dir: str,
                                    completion_kwargs: dict = {}, 
                                    delay_in_seconds: int = 1.0):
        '''
        Request from chatGPT to get high-level solution for question.
        '''
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            messages = [
                {"role": "system", "content": prompter.get_background()},
                {"role": "user", "content": prompter.get_solution_prompt(question=question)}
            ]
            self.logger.debug(f'{task_name}: Requesting for high-level solution...')
            responses = await self.delayed_completion(
                delay_in_seconds = delay_in_seconds,
                messages         = messages,
                **completion_kwargs
            )
            responses = self.get_response_list(responses)
            self.logger.debug(f'{task_name}: Requesting for high-level solution done!')
            for i, response in enumerate(responses):
                with open(pathlib.Path(save_dir, f'{task_name}_{i}.plan'), 'w') as f:
                    f.write(response)
            return responses

    # TODO: Unify request api.
    async def request_for_codes(self,
                                task_name: str,
                                starter_code: str,
                                solution: str,
                                suffix_name: str,
                                prompter: AbstractPrompter,
                                save_dir: str,
                                completion_kwargs: dict = {}, 
                                delay_in_seconds: int = 1.0):
        '''
        Request from chatGPT to get code for high-level solution.
        '''
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            messages = [
                {"role": "system", "content": prompter.get_background()},
                {"role": "user", "content": prompter.get_translation_prompt(starter_code=starter_code, solution=solution)}
            ]
            self.logger.debug(f'{task_name}: Requesting for target code ...')
            responses = await self.delayed_completion(
                delay_in_seconds = delay_in_seconds,
                messages         = messages,
                **completion_kwargs
            )
            response = self.get_response_list(responses)[0]
            response = self.extract_code(response)
            self.logger.debug(f'{task_name}: Requesting for target code of solution done!')
            with open(pathlib.Path(save_dir, f'{task_name}.{suffix_name}'), 'w') as f:
                f.write(response)
            return response


