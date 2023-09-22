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

async def request(semaphone, client, solution, code_request_kwargs):
    async with semaphone:
        codes = await client.request_for_codes(
            solution = solution,
            **code_request_kwargs
        )
        return codes

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--path", help="Path of high-level solution folder", type=str, required=True)
    argparser.add_argument("-j", "--num_workers", help="Number of coroutines for each program", type=int, default=1)
    args = argparser.parse_args()

    solutions = []
    paths = pathlib.Path(args.path).glob("*.plan")
    for path in paths:
        with open(path, 'r') as f:
            solutions.append((path.stem, f.read()))

    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('main')
    client = GPTClient()
    prompter = ANPLPrompter()

    save_dir = args.path.replace("solution", "code") 
    mkdir_override(save_dir)

    rate_limit   = 90000 / 1000 # 90000 tokens, one call less than 1000 tokens
    num_workers  = args.num_workers 
    delay_in_seconds = 60.0 / (rate_limit / num_workers)
    logger.debug(f"Generating target programs for {len(solutions)} solutions...")

    semaphone = asyncio.Semaphore(num_workers)
    async def batch_tasks():
        tasks = []
        for task_name, solution in solutions:
            task = asyncio.create_task(
                request(
                    semaphone,
                    client,
                    code_request_kwargs = {
                        "task_name" : task_name,
                        "completion_kwargs" : {
                            "model"        : "gpt-3.5-turbo-0301",
                            "temperature"       : 0.2,
                            "presence_penalty"  : 0.1,
                        },
                        "starter_code" : "", #TODO: add started code.
                        "suffix_name"  : "anpl",
                        "prompter"     : prompter,
                        "save_dir"     : save_dir,
                        "delay_in_seconds" : delay_in_seconds,
                    },
                    solution = solution
                )
            )
            tasks.append(task)
        for task in tasks:
            try:
                await task
            except Exception as err:
                logger.exception(err)
    asyncio.run(batch_tasks())

