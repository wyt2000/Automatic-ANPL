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

