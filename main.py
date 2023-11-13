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

from Agent import ProgramAgent 
from Strategy import SelfDebugStrategy
from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler
from GPTClient import GPTClient
from CacheManager import CacheManager
from Evaluator import MaxPassEvaluator 
from utils import mkdir_override

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-s", "--save_dir", help="Path to save the results and logs", type=str, required=True)
    args = argparser.parse_args()

    mkdir_override(args.save_dir)
    sampler = HumanEvalProblemSampler()
    max_retry_times = 3
    model_name = "gpt-3.5-turbo-0301"

    with CacheManager(f'{args.save_dir}_cache') as cacheManager: 
        client = GPTClient(cacheManager)
        agent = ProgramAgent(
            client         = client,
            model_name     = model_name,
            evaluator_type = MaxPassEvaluator,
            strategy_type  = SelfDebugStrategy
        )
        for data in sampler.sample_randomly(args.num_problems):
            asyncio.run(
                agent.dispatch(
                    task_name        = data.problem_id,
                    problem_data     = data,
                    save_dir         = args.save_dir,
                    strategy_config  = {
                        'max_restart_times'        : 1,
                        'max_solution_debug_times' : 1,
                        'max_program_debug_times'  : 1,
                    }
                )
            )
 



