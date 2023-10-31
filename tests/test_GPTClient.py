from GPTClient import GPTClient
from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler
from utils import mkdir_no_override
from CacheManager import CacheManager
import asyncio

question_prefix = "Complete the function:\n"

def test_request_for_pretests():
    print("test_request_for_pretests begin!")
    save_dir = 'anpl_test_GPTClient'
    mkdir_no_override(save_dir)
    sampler = HumanEvalProblemSampler()
    question = list(sampler.sample([0]))[0].prompt
    question = question_prefix + question
    with CacheManager('anpl_test_GPTClient_cache') as cacheManager:
        client = GPTClient(cacheManager)
        async def func():
            pretests = await client.request_for_pretests(
                task_name = 'test_request_for_pretests',
                question  = question,
                save_dir  = save_dir,
                num_completions = 100,
                completion_kwargs = {
                    'model'       : "gpt-3.5-turbo-0301", 
                    "temperature" : 0.6,
                }
            )
            print(pretests)
        asyncio.run(func())
    print("test_request_for_pretests end!")
