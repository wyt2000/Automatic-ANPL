from GPTClient import GPTClient
from Prompter.GPTPrompter import GPTPrompter
from Prompter.ANPLPrompter import ANPLPrompter 
from ProblemSampler.APPSProblemSampler import APPSProblemSampler

from utils import mkdir_override
import logging 
import logging.config
import asyncio
import json
import pathlib
import time
import argparse

async def request(semaphone, client, solution_request_kwargs, *args):
    async with semaphone:
        solutions = await client.request_for_solutions(**solution_request_kwargs)
        return solutions 

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-s", "--num_samples", help="Number of high-level solutions for each problem", type=int, default=1)
    argparser.add_argument("-j", "--num_workers", help="Number of coroutines for each problem", type=int, default=1)
    args = argparser.parse_args()

    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('main')
    client = GPTClient()
    sampler = APPSProblemSampler(difficulties=['competition'])
    prompter = ANPLPrompter()

    rate_limit   = 90000 / 1000 # 90000 tokens, one call less than 1000 tokens
    num_problems = args.num_problems 
    num_samples  = args.num_samples 
    num_workers  = args.num_workers 
    delay_in_seconds = 60.0 / (rate_limit / num_workers)

    timestr = time.strftime("%m%d%H%M%S")
    save_dir = f'anpl_apps_solution_{timestr}/'
    mkdir_override(save_dir)

    logger.debug(f"Generating {num_samples} solutions for {num_problems} problems...")
    # sample_list = [3158, 3811, 3876, 3107, 3784, 3621, 3070, 3113, 3665, 3629, 3882, 3075, 3338, 3859, 3888, 3119, 3820, 3633, 3082, 3125, 3833, 3677, 3894, 3087, 3518, 3907, 3900, 3131] 
    semaphone = asyncio.Semaphore(num_workers)
    async def batch_tasks():
        tasks = []
        for data in sampler.sample_randomly(num_problems):
        # for data in sampler.sample(sample_list):
            task = asyncio.create_task(
                request(
                    semaphone,
                    client,
                    solution_request_kwargs = {
                        "task_name" : f"apps_{data.problem_id}",
                        "completion_kwargs" : {
                            "model"  : "gpt-3.5-turbo-0301",
                            "temperature" : 0.6,
                            "n" : num_samples,
                            "logit_bias"    : {755:-100}
                        },
                        "question" : data.question,
                        "prompter" : prompter,
                        "save_dir" : save_dir,
                        "delay_in_seconds" : delay_in_seconds,
                    },
                )
            )
            tasks.append(task)
        for task in tasks:
            try:
                await task
            except Exception as err:
                logger.exception(err)
    asyncio.run(batch_tasks())

