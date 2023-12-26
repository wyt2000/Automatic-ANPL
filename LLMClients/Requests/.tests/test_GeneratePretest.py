from Utils.FileOperations import mkdir_no_override
from Utils import CacheManager
from LLMClients.Clients import GPTClient
from ProblemSamplers import HumanEvalProblemSampler
from Configs import CONFIG

import asyncio
import aiohttp
import openai

def test_request_for_pretests():
    print("\n=== test_request_for_pretests begin ===")
    save_dir = 'anpl_test_GPTClient'
    mkdir_no_override(save_dir)
    sampler = HumanEvalProblemSampler()
    question = list(sampler.sample([0]))[0].question
    with CacheManager('anpl_test_GPTClient_cache', clean=True) as cacheManager:
        client = GPTClient(cacheManager)
        async def func():
            async with aiohttp.ClientSession(trust_env=True) as session:
                openai.aiosession.set(session)
                pretests = await client.GeneratePretest(
                    task_name = 'test_request_for_pretests',
                    question  = question,
                    save_dir  = save_dir,
                    completion_kwargs   = {
                        'model'         : CONFIG.test_model_name,
                        **CONFIG.gen_pretest
                    },
                    num_completions = CONFIG.num_pretests 
                )
            print(len(pretests.splitlines()))
            print(pretests)
        asyncio.run(func())
    print("=== test_request_for_pretests end ===")
