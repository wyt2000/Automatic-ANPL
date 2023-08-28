from GPTClient import GPTClient
from Prompter.GPTPrompter import GPTPrompter
from Prompter.ParselPrompter import ParselPrompter 
from ProblemSampler.APPSProblemSampler import APPSProblemSampler

from utils import mkdir_override
import logging 
import logging.config
import asyncio
import json
import pathlib
import time
import argparse

async def request(semaphone, client, solution_request_kwargs, code_request_kwargs, *args):
    async with semaphone:
        solutions = await client.request_for_solutions(**solution_request_kwargs)
        codes = await client.request_for_codes(
            solutions = solutions,
            **code_request_kwargs
        )
        return codes

async def request_codes_only(semaphone, client, solutions, code_request_kwargs):
    async with semaphone:
        codes = await client.request_for_codes(
            solutions = solutions,
            **code_request_kwargs
        )
        return codes

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger('main')
    client = GPTClient()
    sampler = APPSProblemSampler(difficulties=['all'])
    prompter = ParselPrompter()

    timestr = time.strftime("%m%d%H%M%S")
    save_dir = f'parsel_apps_code_{timestr}/'
    mkdir_override(save_dir)

    rate_limit   = 90000 / 1000 # 90000 tokens, one call less than 1000 tokens
    num_samples  = 2 
    num_workers  = 2 
    num_problems = 5
    delay_in_seconds = 60.0 / (rate_limit / num_workers)
    logger.debug(f"Generating {num_samples} target programs for {num_problems} problems...")

    semaphone = asyncio.Semaphore(num_workers)
    async def batch_tasks():
        tasks = []
        for data in sampler.sample_from_head(num_problems):
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
                    code_request_kwargs = {
                        "task_name" : f"apps_{data.problem_id}",
                        "completion_kwargs" : {
                            "model"        : "gpt-3.5-turbo-0301",
                            "temperature"       : 0.2,
                            "presence_penalty"  : 0.1,
                            "logit_bias"        : {755:-100}
                        },
                        "starter_code" : data.starter_code,
                        "suffix_name"  : "ss",
                        "prompter"     : prompter,
                        "save_dir"     : save_dir,
                        "delay_in_seconds" : delay_in_seconds,
                    }
                )
            )
            tasks.append(task)
        for task in tasks:
            try:
                await task
            except Exception as err:
                logger.exception(err)
    asyncio.run(batch_tasks())

