from Agent import ProgramAgent, SelfDebugStrategy
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

    with CacheManager('anpl_test_Agent_cache', clean=False) as cacheManager:
        client = GPTClient(cacheManager)
        agent = ProgramAgent(client, model_name, MaxPassEvaluator, SelfDebugStrategy)
        asyncio.run(agent.dispatch('anpl_test_Agent', data, save_dir))
                

