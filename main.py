import faulthandler
faulthandler.enable()

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1' 

import sys
sys.setrecursionlimit(10000)

import logging
import logging.config
import argparse
import asyncio
import aiohttp
import openai
import pathlib
import traceback

from Agents import ProgramAgent 
from Strategies import SelfDebugStrategy, FuzzingStrategy
from ProblemSamplers import HumanEvalProblemSampler, HumanEvalProblemData
from GPTClient import GPTClient
from CacheManager import CacheManager
from Evaluators import MaxPassEvaluator, ValidationEvaluator, CodetEvaluator
from utils import mkdir_override, mkdir_no_override, await_with_semaphone

logging.config.fileConfig('Configs/logging.conf')
logger = logging.getLogger('main')

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-j", "--num_workers", help="Number of working coroutines", type=int, default=1)
    argparser.add_argument("-s", "--save_dir", help="Path to save the results and logs", type=str, required=True)
    argparser.add_argument("--use_asserts", help="Generate assertions to debug", action='store_true')
    args = argparser.parse_args()
    save_dir = args.save_dir
    cache_dir = f'{save_dir}_cache'

    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    sampler = HumanEvalProblemSampler()
    model_name = "gpt-3.5-turbo-0301"
    semaphone = asyncio.Semaphore(args.num_workers)

    agent = ProgramAgent()

    sample_list = sampler.sample_randomly(args.num_problems)
    # sample_list = sampler.sample([145])
    async def batch_tasks():
        # Handle SSL Error 
        async with aiohttp.ClientSession(trust_env=True) as session:
            openai.aiosession.set(session)
            tasks = []
            for data in sample_list:
                async def dispatch_coroutine(data: HumanEvalProblemData):
                    save_path = pathlib.Path(save_dir, data.problem_id)
                    cache_path = pathlib.Path(cache_dir, data.problem_id)
                    mkdir_override(save_path)
                    with CacheManager(cache_path) as cacheManager: 
                        client = GPTClient(cacheManager)
                        evaluator = ValidationEvaluator()
                        strategy = SelfDebugStrategy(
                            use_asserts = args.use_asserts
                        )
                        await agent.dispatch(
                            task_name        = data.problem_id,
                            save_dir         = save_path,
                            problem_data     = data,
                            client           = client,
                            model_name       = model_name,
                            evaluator        = evaluator,
                            strategy         = strategy,
                        )
                task = asyncio.create_task(
                    await_with_semaphone(dispatch_coroutine, semaphone, data)
                )
                tasks.append(task)
            for task in tasks:
                try:
                    await task
                except Exception as err:
                    traceback.print_exc()                

    asyncio.run(batch_tasks())        
 
