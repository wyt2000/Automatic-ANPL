import openai
import logging 
import logging.config
import aiohttp
import pathlib
import json
import asyncio
import re
import ast
from Prompter import Prompter
from Synthesizer.ANPLSynthesizer import verify_code
from utils import extract_code, extract_func, extract_asserts 
from Tracer import IOExample
from typing import Callable
from CacheManager import CacheManager
from functools import reduce

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

    # Ask GPT for complelations
    async def request(self,
                      task_name: str,
                      task_kind: str, 
                      prompt_background: str,
                      prompt_template: str, 
                      prompt_kwargs: dict = {},
                      response_verifier: Callable[[str], bool] = lambda _ : True,
                      response_handlers: list[Callable[[str], str]] = [],
                      completion_kwargs: dict = {},
                      num_completions: int = 1,
                      retry_times: int = 1) -> list[str] | None:

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

        # Request for remaining responses and verify them.
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
                responses.extend(filter(response_verifier, new_responses))
        self.logger.debug(f'{task_name}: [{task_kind}] request done!')

        # Save raw responses in cache.
        self.cacheManager.save(task_kind, responses, *cache_key)
        
        # Convert responses to valid format or save them in files.
        for handler in response_handlers:
            responses = map(handler, responses)
        return responses

    # Request from chatGPT to get pretests for question.
    async def request_for_pretests(self,
                                   task_name: str,
                                   question: str,
                                   save_dir: str,
                                   completion_kwargs: dict,
                                   num_completions: int):

        responses = await self.request(
            task_name               = task_name,
            task_kind               = 'pretest',
            prompt_background       = Prompter.background,
            prompt_template         = Prompter.pretest_prompt,
            prompt_kwargs           = {'question' : question},
            response_handlers       = [extract_code, extract_asserts],
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions 
        )
        
        # Split and remove duplicated assert statements.
        asserts = set()
        for response in responses:
            for assert_stmt in response.splitlines():
                asserts.add(assert_stmt)

        with open(pathlib.Path(save_dir, f'{task_name}.pretest'), 'w') as f:
            f.write('\n'.join(asserts))

        return asserts 

    # Request from chatGPT to get high-level solution for question.
    async def request_for_solutions(self,
                                    task_name: str,
                                    question: str,
                                    save_dir: str,
                                    completion_kwargs: dict,
                                    num_completions: int):

        responses = await self.request(
            task_name               = task_name,
            task_kind               = 'solution',
            prompt_background       = Prompter.background,
            prompt_template         = Prompter.solution_prompt,
            prompt_kwargs           = {'question' : question},
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions 
        )

        for i, response in enumerate(responses):
            with open(pathlib.Path(save_dir, f'{task_name}_{i}.plan'), 'w') as f:
                f.write(response)
        return responses

"""
    # TODO: Unify request api.
    # TODO: Refactor program verification.
    async def request_for_codes(self,
                                task_name: str,
                                starter_code: str,
                                func_name: str,
                                question: str,
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
                {"role": "user", "content": prompter.get_translation_prompt(starter_code=starter_code, question=question, solution=solution, func_name=func_name)}
            ]
            self.logger.debug(f'{task_name}: Requesting for target code ...')
            for i in range(self.retry_times):
                raw_responses = await self.delayed_completion(
                    task_name        = task_name,
                    delay_in_seconds = delay_in_seconds,
                    messages         = messages,
                    **completion_kwargs
                )
                raw_response = self.get_response_list(raw_responses)[0]
                response = self.extract_code(raw_response)
                try:
                    verify_code(response, func_name)
                except Exception as err:
                    self.logger.exception(err)
                    self.logger.debug(raw_response)
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
            return responses

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
