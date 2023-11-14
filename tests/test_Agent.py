from Agent import ProgramAgent 
from Strategy import SelfDebugStrategy
from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler
from GPTClient import GPTClient
from CacheManager import CacheManager
from Evaluator import MaxPassEvaluator 
from utils import mkdir_override

import asyncio
import logging
import logging.config

logging.config.fileConfig('logging.conf')
model_name = "gpt-3.5-turbo-0301"
save_dir = 'anpl_test_Agent'

def test_ProgramAgent():
    mkdir_override(save_dir)
    sampler = HumanEvalProblemSampler()
    data = list(sampler.sample([163]))[0]
    evaluator = MaxPassEvaluator()
    strategy = SelfDebugStrategy(
        max_restart_times        = 1,
        max_solution_debug_times = 1,
        max_program_debug_times  = 1
    )

    with CacheManager('anpl_test_Agent_cache', clean=False) as cacheManager:
        client = GPTClient(cacheManager)
        agent = ProgramAgent()
        asyncio.run(
            agent.dispatch(
                task_name        = 'anpl_test_Agent',
                save_dir         = save_dir,
                problem_data     = data,
                client           = client,
                model_name       = model_name,
                evaluator        = evaluator,
                strategy         = strategy,
            )
        )
                

