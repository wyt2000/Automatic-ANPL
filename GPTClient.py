import openai
import logging 
import logging.config
import aiohttp
import pathlib
import json
import asyncio
import re
import ast
from functools import partial
from typing import Callable, Any

from Prompter import Prompter
from utils import extract_code, extract_func, extract_asserts, verify_anpl, collect_anpl, verify_python
from Tracer import IOExample
from CacheManager import CacheManager

class GPTClient:

    def __init__(self,
                 cacheManager: CacheManager,
                 retry_times=5,
                 retry_interval=10):

        self.logger = logging.getLogger(__name__)
        self.retry_times = retry_times
        self.retry_interval = retry_interval
        self.cacheManager = cacheManager 

    # Async create `ChatCompletion`, backoff when reach time limit
    async def delayed_completion(self, task_name, messages, **kwargs):
        for i in range(self.retry_times):
            try:
                responses = await openai.ChatCompletion.acreate(
                    messages = messages,
                    **kwargs
                )
                return responses
            except openai.error.InvalidRequestError as err:
                self.logger.debug(f'{task_name}: InvalidRequestError!')
                raise err
            except openai.error.RateLimitError as err:
                await asyncio.sleep(self.retry_interval * (2 ** i))
        raise openai.error.RateLimitError

    # Convert GPT responses to list[str]
    @staticmethod
    def get_response_list(responses: str):
        return [response["message"]["content"] for response in responses["choices"]]

    # Save response to file
    @staticmethod
    def save_one(result: str, save_dir: str, filename: str):
        with open(pathlib.Path(save_dir, filename), 'w') as f:
            f.write(result)

    # Save responses to files named as 0 to n - 1
    @staticmethod
    def save_all(results: list[str], save_dir: str, filename: str):
        for i, response in enumerate(results):
            with open(pathlib.Path(save_dir, filename.format(i=i)), 'w') as f:
                f.write(response)

    # Ask GPT for complelations
    async def _request(self,
                      task_name: str,
                      task_kind: str, 
                      prompt_template: str, 
                      prompt_kwargs: dict = {},
                      prompt_background: str = Prompter.background,
                      response_verifier: Callable[[str], bool] = lambda _ : True,
                      response_handlers: list[Callable[[str], str]] = [],
                      response_collector: Callable[list[str], Any] = lambda x : x,
                      response_saver: Callable[Any, None] = lambda _ : None,
                      completion_kwargs: dict = {},
                      num_completions: int = 1,
                      retry_times: int = 1) -> Any:

        # Look up cache and load at most `num_completions` responses.
        responses = []
        cache_key = (task_name, prompt_template, prompt_kwargs, completion_kwargs)
        if (cache_value := self.cacheManager.load(task_kind, *cache_key)) is not None:
            self.logger.debug(f'{task_name}: [{task_kind}] cache hit!')
            if len(cache_value) >= num_completions:
                cache_value = cache_value[:num_completions]
            responses.extend(cache_value)

        # Build up prompts.
        messages = [
            {"role": "system", "content": prompt_background},
            {"role": "user", "content": prompt_template.format(**prompt_kwargs)}
        ]

        # Request for remaining responses, extract the results and verify them.
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            for i in range(retry_times):
                if len(responses) == num_completions:
                    break
                self.logger.debug(f'{task_name}: [{task_kind}] requesting for {num_completions-len(responses)} responses...')
                new_responses = await self.delayed_completion(
                    task_name        = task_name,
                    messages         = messages,
                    n                = num_completions - len(responses),
                    **completion_kwargs
                )
                new_responses = GPTClient.get_response_list(new_responses)
                for handler in response_handlers:
                    new_responses = list(map(handler, new_responses))
                responses.extend(filter(response_verifier, new_responses))
        self.logger.debug(f'{task_name}: [{task_kind}] request done!')

        # Save raw responses in cache.
        self.cacheManager.save(task_kind, responses, *cache_key)
        
        # Convert responses to compact format and save them in files.
        responses = response_collector(responses)
        response_saver(responses)
        return responses

    # Request from chatGPT to get pretests for question.
    async def request_for_pretests(self,
                                   task_name: str,
                                   question: str,
                                   save_dir: str,
                                   completion_kwargs: dict,
                                   num_completions: int):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'pretest',
            prompt_template         = Prompter.pretest_prompt,
            prompt_kwargs           = {'question' : question},
            response_handlers       = [extract_code, extract_asserts],
            response_collector      = lambda res : '\n'.join(set(stmt for r in res for stmt in r.splitlines())),
            response_saver          = partial(GPTClient.save_one, save_dir=save_dir, filename=f'{task_name}.test'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions 
        )

    # Request from chatGPT to get high-level solution for question.
    async def request_for_solutions(self,
                                    task_name: str,
                                    question: str,
                                    save_dir: str,
                                    completion_kwargs: dict,
                                    num_completions: int):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'solution',
            prompt_template         = Prompter.solution_prompt,
            prompt_kwargs           = {'question' : question},
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.plan'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions 
        )

    # Request from chatGPT to get code for high-level solution.
    async def request_for_codes(self,
                                task_name: str,
                                entry_point: str,
                                question: str,
                                solution: str,
                                save_dir: str,
                                completion_kwargs: dict,
                                num_completions: int,
                                retry_times: int = 5):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'translation',
            prompt_template         = Prompter.translation_prompt,
            prompt_kwargs           = {'question' : question, 'solution' : solution, 'entry_point' : entry_point},
            response_verifier       = partial(verify_anpl, entry_point=entry_point),
            response_handlers       = [extract_code],
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.anpl'),
            response_collector      = lambda res : list(map(partial(collect_anpl, entry_point=entry_point), res)),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
            retry_times             = retry_times
        )

    # Request from chatGPT to get function completions from hole.
    async def request_for_function_completions(self,
                                               task_name: str,
                                               prefix: str,
                                               code: str,
                                               hole: str,
                                               target: str,
                                               func_names: set[str],
                                               completion_kwargs: dict,
                                               num_completions: int):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'function_completion',
            prompt_template         = Prompter.function_completion_prompt,
            prompt_kwargs           = {'prefix' : prefix, 'code' : code, 'hole' : hole},
            response_handlers       = [extract_code, partial(extract_func, target=target, func_names=func_names)],
            response_collector      = lambda res : list(set(filter(verify_python, res))),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions
        )

    async def request_for_counterexamples(self,
                                          task_name: str,
                                          question: str,
                                          program: str,
                                          prompter: AbstractPrompter,
                                          save_dir: str,
                                          completion_kwargs: dict = {}, 
                                          delay_in_seconds: float = 1.0):
        return await self._request(
            task_name               = task_name,
            task_kind               = 'function_completion',
            prompt_template         = Prompter.function_completion_prompt,
            prompt_kwargs           = {'prefix' : prefix, 'code' : code, 'hole' : hole},
            response_handlers       = [extract_code, partial(extract_func, target=target, func_names=func_names)],
            response_collector      = lambda res : list(set(filter(verify_python, res))),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions
        )

"""
    async def request_for_debugged_function(self,
                                            task_name: str,
                                            question: str,
                                            solution: str,
                                            program: str,
                                            func_name: str,
                                            holes: set[str],
                                            func_code: str,
                                            func_traces: list[IOExample],
                                            prompter: AbstractPrompter,
                                            save_dir: str,
                                            completion_kwargs: dict = {}, 
                                            delay_in_seconds: float = 1.0):
        '''
        Request from chatGPT to get repaired function by solution, program and traces.
        '''
        # Add trace before function code
        function_with_traces = "# Trace: \n"
        for trace in func_traces:
            function_with_traces += f"# {repr(trace)}\n"
        function_with_traces += func_code
        
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            messages = [
                {"role": "system", "content": prompter.get_background()},
                {"role": "user", "content": prompter.get_function_debug_prompt(question=question, solution=solution, func_name=func_name, program=program, function_with_traces=function_with_traces)}
            ]
            responses = await self.delayed_completion(
                task_name        = task_name,
                delay_in_seconds = delay_in_seconds,
                messages         = messages,
                **completion_kwargs
            )
            responses = self.get_response_list(responses)
            for i, response in enumerate(responses):
                responses[i] = self.extract_func(response, func_name, holes)
            return responses

    async def request_for_debugged_solution(self,
                                            task_name: str,
                                            question: str,
                                            old_solution: str,
                                            counterexample: str,
                                            prompter: AbstractPrompter,
                                            save_dir: str,
                                            completion_kwargs: dict = {}, 
                                            delay_in_seconds: float = 1.0):
        '''
        Request from chatGPT to get repaired high-level solution for question and counterexample.
        '''
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            messages = [
                {"role": "system", "content": prompter.get_background()},
                {"role": "user", "content": prompter.get_solution_debug_prompt(question=question, solution=old_solution, counterexample=counterexample)}
            ]
            self.logger.debug(f'{task_name}: Requesting for debugged high-level solution...')
            responses = await self.delayed_completion(
                task_name        = task_name,
                messages         = messages,
                **completion_kwargs
            )
            response = self.get_response_list(responses)[0]
            self.logger.debug(f'{task_name}: Requesting for debugged high-level solution done!')
            with open(pathlib.Path(save_dir, f'{task_name}.plan'), 'w') as f:
                f.write(response)
            return response
"""

if __name__ == '__main__':
    client = GPTClient()
    code = '''

abc
```
def
sdfsdafsdsa
fadsfsafs
sfadfsafa
```
xyz

'''
    code = client.extract_code(code)
    print(code)
