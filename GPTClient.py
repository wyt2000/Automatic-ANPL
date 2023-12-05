import openai
import logging 
import logging.config
import pathlib
import json
import asyncio
import re
import ast
from functools import partial
from typing import Callable, Any

from Prompter import Prompter
from utils import extract_code, extract_anpl, extract_func, extract_asserts, verify_anpl, collect_anpl, verify_python, verify_counterexample, collect_counterexample, compose_function_with_traces, remove_asserts, collect_anpl_with_asserts, verify_input_generator, collect_random_input, extract_validator
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
            except (openai.error.RateLimitError, openai.error.APIConnectionError) as err:
                await asyncio.sleep(self.retry_interval * (2 ** i))
        raise openai.error.RateLimitError

    # Convert GPT responses to list[str]
    @staticmethod
    def get_response_list(responses: str):
        return [response["message"]["content"] for response in responses["choices"]]

    # Save response to file
    @staticmethod
    def save_one(result: Any, save_dir: str, filename: str):
        with open(pathlib.Path(save_dir, filename), 'w') as f:
            f.write(str(result))

    # Save responses to files named as 0 to n - 1
    @staticmethod
    def save_all(results: list[Any], save_dir: str, filename: str):
        for i, response in enumerate(results):
            with open(pathlib.Path(save_dir, filename.format(i=i)), 'w') as f:
                f.write(str(response))

    # Abstract request GPT for completions.
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
                      retry_times: int = 1,
                      verbose: bool = True) -> Any:

        # Whether output logs or not
        logger = self.logger if verbose else logging.getLogger('dummy')

        # Look up cache and load at most `num_completions` responses.
        responses = []
        prompt = prompt_template.format(**prompt_kwargs)
        cache_key = (task_name, prompt, sorted(completion_kwargs.items()))
        if (cache_value := self.cacheManager.load(task_kind, *cache_key)) is not None:
            logger.debug(f'{task_name}: [{task_kind}] cache hit!')
            responses.extend(cache_value)

        # Build up prompts.
        messages = [
            {"role": "system", "content": prompt_background},
            {"role": "user", "content": prompt}
        ]
        # Request for remaining responses, extract the results and verify them.
        for i in range(retry_times):
            if len(responses) >= num_completions:
                break
            logger.debug(f'{task_name}: [{task_kind}] requesting for {num_completions-len(responses)} responses...')
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
        responses = responses[:num_completions]
        logger.debug(f'{task_name}: [{task_kind}] request done!')

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
                                   num_completions: int,
                                   retry_times: int = 5):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'pretest',
            prompt_template         = Prompter.pretest_prompt,
            prompt_kwargs           = {'question' : question},
            response_handlers       = [extract_code, extract_asserts],
            response_verifier       = lambda assert_str : len(assert_str) > 0,
            response_collector      = lambda res : '\n'.join(sorted(set(stmt for r in res for stmt in r.splitlines()))),
            response_saver          = partial(GPTClient.save_one, save_dir=save_dir, filename=f'{task_name}.test'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
            retry_times             = retry_times
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
    async def request_for_anpl_codes(self,
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
            response_handlers       = [extract_code, partial(extract_anpl, question=question)],
            response_verifier       = partial(verify_anpl, entry_point=entry_point),
            response_collector      = lambda res : list(map(partial(collect_anpl, entry_point=entry_point), res)),
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.anpl'),
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
                                               use_asserts: bool,
                                               completion_kwargs: dict,
                                               num_completions: int):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'function_completion',
            prompt_template         = Prompter.function_completion_prompt_with_asserts if use_asserts
                                      else Prompter.function_completion_prompt,
            prompt_kwargs           = {'prefix' : prefix, 'code' : code, 'hole' : hole, 'func_name' : target},
            response_handlers       = [
                extract_code,
                partial(extract_func, target=target, func_names=func_names),
                partial(remove_asserts, func_name=target)
            ],
            response_collector      = lambda res : sorted(set(filter(verify_python, res))),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
        )

    # Request from chatGPT to get counterexamples of the program.
    async def request_for_counterexamples(self,
                                          task_name: str,
                                          question: str,
                                          program: str,
                                          entry_point: str,
                                          save_dir: str,
                                          completion_kwargs: dict,
                                          num_completions: int,
                                          retry_times: int = 5):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'counterexamples',
            prompt_template         = Prompter.counterexample_prompt,
            prompt_kwargs           = {'question' : question, 'program' : program},
            response_handlers       = [extract_code, extract_asserts],
            response_verifier       = partial(verify_counterexample, program=program, entry_point=entry_point),
            response_collector      = lambda res : list(map(partial(collect_counterexample, program=program, entry_point=entry_point), res)),
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.counterexample'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
            retry_times             = retry_times
        )
    
    # Request from chatGPT to get repaired function by solution, program and traces.
    async def request_for_debugged_function(self,
                                            task_name: str,
                                            question: str,
                                            solution: str,
                                            program: str,
                                            target: str,
                                            func_names: set[str],
                                            func_code: str,
                                            func_traces: list[IOExample],
                                            save_dir: str,
                                            completion_kwargs: dict,
                                            num_completions: int):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'function_debug',
            prompt_template         = Prompter.function_debug_prompt,
            prompt_kwargs           = {'question' : question, 'solution' : solution, 'program' : program, 'function_with_traces' : compose_function_with_traces(func_code, func_traces), 'func_name' : target},
            response_handlers       = [
                extract_code,
                partial(extract_func, target=target, func_names=func_names),
                partial(remove_asserts, func_name=target)
            ],
            response_collector      = lambda res : sorted(set(filter(verify_python, res))),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
        )

    # Request from chatGPT to get repaired high-level solution for question and counterexample.
    async def request_for_debugged_solution(self,
                                            task_name: str,
                                            question: str,
                                            old_solution: str,
                                            counterexample: str,
                                            save_dir: str,
                                            completion_kwargs: dict,
                                            num_completions: int):
        return await self._request(
            task_name               = task_name,
            task_kind               = 'solution_debug',
            prompt_template         = Prompter.solution_debug_prompt,
            prompt_kwargs           = {'question' : question, 'solution' : old_solution, 'counterexample' : counterexample},
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.fixed_plan'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions
        )

    # Request from chatGPT to add assertions for the function.
    async def request_for_assertions(self,
                                     task_name: str,
                                     question: str,
                                     solution: str,
                                     anpl_code: str,
                                     entry_point: str,
                                     func_code: str,
                                     func_names: set[str],
                                     save_dir: str,
                                     completion_kwargs: dict,
                                     num_completions: int,
                                     retry_times: int = 5):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'assertion',
            prompt_template         = Prompter.assertion_prompt,
            prompt_kwargs           = {'question' : question, 'solution' : solution, 'program' : anpl_code, 'function' : func_code, 'func_name' : entry_point},
            response_handlers       = [
                extract_code,
                partial(extract_func, target=entry_point, func_names=func_names),
                partial(remove_asserts, func_name=entry_point)
            ],
            response_verifier       = verify_python,
            response_collector      = lambda res : list(map(partial(collect_anpl_with_asserts, anpl_code=anpl_code, entry_point=entry_point), res)),
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.anpl_with_asserts'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
            retry_times             = retry_times
        )

    # Request from chatGPT to get the input or output constraints.
    async def request_for_io_constraint(self,
                                        task_name: str,
                                        function: str,
                                        io_type: str,
                                        save_dir: str,
                                        completion_kwargs: dict,
                                        num_completions: int):

        return await self._request(
            task_name               = task_name,
            task_kind               = f'{io_type}_constraint',
            prompt_template         = Prompter.io_constraint_prompt,
            prompt_kwargs           = {'function' : function, 'io_type' : io_type},
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.{io_type}_constraint'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions 
        )
        
    # Request from chatGPT to generate random inputs.
    async def request_for_random_input(self,
                                       task_name: str,
                                       func_name: str,
                                       func_code: str,
                                       constraint: str,
                                       num_random_inputs: int,
                                       save_dir: str,
                                       completion_kwargs: dict,
                                       num_completions: int,
                                       retry_times: int = 5):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'random_input',
            prompt_template         = Prompter.random_input_prompt,
            prompt_kwargs           = {'func_name': func_name, 'function': func_code, 'constraint': constraint},
            response_handlers       = [extract_code],
            response_verifier       = partial(verify_input_generator, func_name=f'test_{func_name}'),
            response_collector      = partial(collect_random_input, func_name=f'test_{func_name}', num_random_inputs=num_random_inputs),
            response_saver          = partial(GPTClient.save_one, save_dir=save_dir, filename=f'{task_name}.random_input'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
            retry_times             = retry_times
        )

    # Request from chatGPT to validate the function.
    async def request_for_validator(self,
                                    task_name: str,
                                    func_name: str,
                                    func_code: str,
                                    save_dir: str,
                                    completion_kwargs: dict,
                                    num_completions: int,
                                    retry_times: int = 5):

        return await self._request(
            task_name               = task_name,
            task_kind               = 'validator',
            prompt_template         = Prompter.validator_prompt,
            prompt_kwargs           = {'func_name': func_name, 'function': func_code},
            response_handlers       = [extract_code, extract_validator],
            response_verifier       = verify_python,
            response_saver          = partial(GPTClient.save_all, save_dir=save_dir, filename=f'{task_name}.{{i}}.validator'),
            completion_kwargs       = completion_kwargs,
            num_completions         = num_completions,
            retry_times             = retry_times
        )

