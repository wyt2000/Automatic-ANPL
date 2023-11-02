from GPTClient import GPTClient
from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler
from utils import mkdir_no_override
from CacheManager import CacheManager
import asyncio
import logging
import logging.config

logging.config.fileConfig('logging.conf')

model_name = "gpt-3.5-turbo-0301"
question_prefix = "Complete the function:\n"

def test_request_for_pretests():
    print("\n=== test_request_for_pretests begin ===")
    save_dir = 'anpl_test_GPTClient'
    mkdir_no_override(save_dir)
    sampler = HumanEvalProblemSampler()
    question = list(sampler.sample([0]))[0].prompt
    question = question_prefix + question
    with CacheManager('anpl_test_GPTClient_cache', clean=True) as cacheManager:
        client = GPTClient(cacheManager)
        async def func():
            pretests = await client.request_for_pretests(
                task_name = 'test_request_for_pretests',
                question  = question,
                save_dir  = save_dir,
                completion_kwargs = {
                    'model'       : model_name,
                    "temperature" : 0.6,
                },
                num_completions = 100,
            )
            print(pretests)
        asyncio.run(func())
    print("=== test_request_for_pretests end ===")

def test_request_for_solutions():
    print("\n=== test_request_for_solutions begin ===")
    save_dir = 'anpl_test_GPTClient'
    mkdir_no_override(save_dir)
    sampler = HumanEvalProblemSampler()
    question = list(sampler.sample([0]))[0].prompt
    question = question_prefix + question
    with CacheManager('anpl_test_GPTClient_cache', clean=True) as cacheManager:
        client = GPTClient(cacheManager)
        async def func():
            solutions = await client.request_for_solutions(
                task_name = 'test_request_for_solutions',
                question  = question,
                save_dir  = save_dir,
                completion_kwargs = {
                    'model'       : model_name, 
                    "temperature" : 0.6,
                    "logit_bias"  : {755:-100},
                },
                num_completions = 1,
            )
            print(solutions[0])
        asyncio.run(func())
    print("=== test_request_for_solutions end ===")

solution = '''1. Sort the given list of numbers in ascending order.
2. Initialize a variable "previous" to the first element of the sorted list.
3. Loop through the sorted list from the second element to the end.
4. For each element, check if the difference between it and the "previous" element is less than the given threshold.
5. If the difference is less than the threshold, return True.
6. If the loop completes without finding any close elements, return False.
'''

def test_request_for_codes():
    print("\n=== test_request_for_codes begin ===")
    save_dir = 'anpl_test_GPTClient'
    mkdir_no_override(save_dir)
    sampler = HumanEvalProblemSampler()
    data = list(sampler.sample([0]))[0]
    question = data.prompt
    question = question_prefix + question
    entry_point = data.entry_point
    with CacheManager('anpl_test_GPTClient_cache', clean=True) as cacheManager:
        client = GPTClient(cacheManager)
        async def func():
            codes = await client.request_for_codes(
                task_name = 'test_request_for_codes',
                entry_point = entry_point,
                question  = question,
                solution  = solution,
                save_dir  = save_dir,
                completion_kwargs = {
                    "model"             : model_name,
                    "temperature"       : 0.2,
                    "presence_penalty"  : 0.1,
                },
                num_completions = 1
            )
            print(codes[0])
        asyncio.run(func())
    print("=== test_request_for_codes end ===")

code = '''from typing import List

def sort_numbers(numbers: List[float]) -> List[float]:
    """Sorts the given list of numbers in ascending order."""

def check_close_elements(numbers: List[float], threshold: float) -> bool:
    """Checks if any two numbers in the given list are closer to each other than the given threshold."""

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
    sorted_numbers = sort_numbers(numbers)
    return check_close_elements(sorted_numbers, threshold)
'''

func_names = {'has_close_elements', 'check_close_elements', 'sort_numbers'}

hole = '''def check_close_elements(numbers: List[float], threshold: float) -> bool:
    """Checks if any two numbers in the given list are closer to each other than the given threshold."""
'''

target = 'check_close_elements'

def test_request_for_function_completions():
    print("\n=== test_request_for_function_completions begin ===")
    save_dir = 'anpl_test_GPTClient'
    mkdir_no_override(save_dir)
    with CacheManager('anpl_test_GPTClient_cache', clean=True) as cacheManager:
        client = GPTClient(cacheManager)
        async def func():
            codes = await client.request_for_function_completions(
                task_name = 'test_request_for_function_completions',
                prefix = '',
                code = code,
                hole = hole,
                target = target,
                func_names = func_names,
                completion_kwargs = {
                    "model"             : model_name,
                    "temperature"       : 0.6,
                },
                num_completions = 1
            )
            print(codes[0])
        asyncio.run(func())
    print("=== test_request_for_function_completions end ===")

