from GPTClient import GPTClient
from ProblemSampler.APPSProblemSampler import APPSProblemSampler, APPSProblemData
from Prompter.ANPLPrompter import ANPLPrompter 
from Prompter.Prompter import AbstractPrompter
from utils import mkdir_override

import logging
import logging.config
import argparse
import asyncio
import json
import pathlib
import time

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

async def solve_problem(client: GPTClient,
                  prompter: AbstractPrompter,
                  data: APPSProblemData,
                  num_golden_ios: int,
                  save_dir: str,
                  delay_in_seconds: int = 1,
                  max_restart_times: int = 1):
    task_name = f"apps_{data.problem_id}"
    logger.debug(f"{task_name}: start solving the problem...")
    mkdir_override(save_dir)
    restart_times = 0
    while restart_times < max_restart_times:
        # Generate fake golden io
        golden_ios = await client.request_for_golden_io(
            task_name = task_name,
            completion_kwargs = {
                "model"  : "gpt-3.5-turbo-0301",
                "temperature" : 0.6,
                "n" : num_golden_ios,
            },
            question  = data.question,
            prompter  = prompter,
            save_dir  = save_dir,
            delay_in_seconds = delay_in_seconds
        )
        logger.debug(golden_ios)
        restart_times += 1
    

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-s", "--num_golden_ios", help="Number of golden io for each problem", type=int, default=1)
    args = argparser.parse_args()

    sampler = APPSProblemSampler(difficulties=['competition'])
    client = GPTClient()
    prompter = ANPLPrompter()

    timestr = time.strftime("%m%d%H%M%S")
    save_prefix = f'anpl_apps_{timestr}'
    mkdir_override(save_prefix)

    logger.debug(f"There are {args.num_problems} problems to be solved!") 
    for data in sampler.sample_randomly(args.num_problems):
        try:
            save_dir = pathlib.Path(save_prefix, f'{data.problem_id}')
            asyncio.run(
                solve_problem(
                    client,
                    prompter,
                    data,
                    args.num_golden_ios,
                    str(save_dir)
                )
            )
        except Exception as err:
            logger.exception(err)

