import openai
import logging 
import logging.config
import aiohttp
import pathlib
import json
import asyncio
import re
from Prompter.Prompter import AbstractPrompter
from Synthesizer.ANPLSynthesizer import verify_code
from utils import Cache

class GPTClient:

    def __init__(self,
                 retry_times=10,
                 retry_interval=5,
                 cache_path='cache.json'):

        self.logger = logging.getLogger(__name__)
        self.pattern = re.compile("^\s*[^\d\W]\w*\(.*\).*\:\s*(.*)")
        self.retry_times = retry_times
        self.retry_interval = retry_interval
        self.cache = Cache(cache_path)

    async def delayed_completion(self, task_name, delay_in_seconds, messages, use_cache=True, **kwargs):
        '''
        Delay `delay_in_seconds`, then async call `ChatCompletion`.
        '''
        cache_key = (task_name, messages)
        # Look up cache
        if use_cache and (cache_value := self.cache.load(*cache_key)) is not None:
            self.logger.debug(f"{task_name}: Cache hit!")
            return cache_value

        # Wait and send request
        await asyncio.sleep(delay_in_seconds)
        for i in range(self.retry_times):
            try:
                response = await openai.ChatCompletion.acreate(
                    messages = messages,
                    **kwargs
                )
                if use_cache:
                    self.cache.save(response, *cache_key)
                return response
            except openai.error.InvalidRequestError as err:
                self.logger.debug(f"{task_name}: InvalidRequestError!")
                raise err
            except Exception as err:
                self.logger.exception(err)
                await asyncio.sleep(self.retry_interval)
                self.logger.debug(f"{task_name}: Retry {i + 1} times.")

    def get_response_list(self, responses):
        '''
        Convert GPT responses to list[str]
        '''
        return [response["message"]["content"] for response in responses["choices"]]

    def extract_code(self, response: str):
        return response.strip('`')

    def extract_io(self, response: str):
        inp, out = [], []
        isinp, isout = False, False 
        for line in response.splitlines():
            if '-Input-' in line:
                isinp, isout = True, False
                continue
            if '-Output-' in line:
                isout, isinp = True, False
                continue
            if isinp:
                inp.append(line)
            elif isout:
                out.append(line)
        return '\n'.join(inp), '\n'.join(out)

    async def request_for_solutions(self,
                                    task_name: str,
                                    question: str,
                                    prompter: AbstractPrompter,
                                    save_dir: str,
                                    completion_kwargs: dict = {}, 
                                    delay_in_seconds: float = 1.0):
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
                task_name        = task_name,
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
    # TODO: Refactor program verification.
    async def request_for_codes(self,
                                task_name: str,
                                starter_code: str,
                                solution: str,
                                suffix_name: str,
                                prompter: AbstractPrompter,
                                save_dir: str,
                                completion_kwargs: dict = {}, 
                                delay_in_seconds: float = 1.0):
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
            for i in range(self.retry_times):
                responses = await self.delayed_completion(
                    task_name        = task_name,
                    delay_in_seconds = delay_in_seconds,
                    messages         = messages,
                    **completion_kwargs
                )
                response = self.get_response_list(responses)[0]
                response = self.extract_code(response)
                try:
                    verify_code(response)
                except Exception as err:
                    self.logger.exception(err)
                    self.logger.debug(f'{task_name}: Invalid target code! Retry {i + 1} times.')
                    continue
                self.logger.debug(f'{task_name}: Requesting for target code of solution done!')
                with open(pathlib.Path(save_dir, f'{task_name}.{suffix_name}'), 'w') as f:
                    f.write(response)
                return response

    async def request_for_counterexamples(self,
                                          task_name: str,
                                          question: str,
                                          program: str,
                                          prompter: AbstractPrompter,
                                          save_dir: str,
                                          completion_kwargs: dict = {}, 
                                          delay_in_seconds: float = 1.0):
        '''
        Request from chatGPT to get counterexample for question and program.
        '''
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            messages = [
                {"role": "system", "content": prompter.get_background()},
                {"role": "user", "content": prompter.get_counterexample_prompt(question=question, program=program)}
            ]
            self.logger.debug(f'{task_name}: Requesting for counterexample...')
            responses = await self.delayed_completion(
                task_name        = task_name,
                delay_in_seconds = delay_in_seconds,
                messages         = messages,
                **completion_kwargs
            )
            responses = self.get_response_list(responses)
            responses = [self.extract_io(response) for response in responses]
            self.logger.debug(f'{task_name}: Requesting for counterexample done!')
            for i, response in enumerate(responses):
                with open(pathlib.Path(save_dir, f'{task_name}_{i}.io'), 'w') as f:
                    f.write(json.dumps(response))
            return responses


if __name__ == '__main__':
    client = GPTClient()
    io = '''-----Input-----
3
1 1 1
2 0 2
3 1 1
-----Output-----
1
8
4'''
    io = client.extract_io(io)
    print(io)
