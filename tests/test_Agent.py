from Agent import ProgramAgent, SelfDebugStrategy
from GPTClient import GPTClient
from CacheManager import CacheManager
from Evaluator import MaxPassEvaluator 
import asyncio

model_name = "gpt-3.5-turbo-0301"

def test_ProgramAgent():
    with CacheManager('anpl_test_Agent_cache', clean=True) as cacheManager:
        client = GPTClient(cacheManager)
        agent = ProgramAgent(client, model_name, MaxPassEvaluator, SelfDebugStrategy)
        asyncio.run(agent.dispatch('anpl_test_Agent', None, 'anpl_test_Agent'))
                

