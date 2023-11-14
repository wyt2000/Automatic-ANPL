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
import pathlib

from Agent import ProgramAgent 
from Strategy import SelfDebugStrategy
from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler
from GPTClient import GPTClient
from CacheManager import CacheManager
from Evaluator import MaxPassEvaluator 
from utils import mkdir_override, mkdir_no_override

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-s", "--save_dir", help="Path to save the results and logs", type=str, required=True)
    args = argparser.parse_args()
    save_dir = args.save_dir
    cache_dir = f'{save_dir}_cache'

    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    sampler = HumanEvalProblemSampler()
    model_name = "gpt-3.5-turbo-0301"
    #sample_list = sampler.sample_randomly(args.num_problems)
    sample_list = list(sampler.sample_randomly(args.num_problems))[1:]

    for data in sample_list:
        save_path = pathlib.Path(save_dir, data.problem_id)
        cache_path = pathlib.Path(cache_dir, data.problem_id)
        mkdir_override(save_path)
        with CacheManager(cache_path) as cacheManager: 
            client = GPTClient(cacheManager)
            agent = ProgramAgent(
                client         = client,
                model_name     = model_name,
                evaluator_type = MaxPassEvaluator,
                strategy_type  = SelfDebugStrategy
            )
            asyncio.run(
                agent.dispatch(
                    task_name        = data.problem_id,
                    problem_data     = data,
                    save_dir         = save_path
                )
            )
 



