from GPTClient import GPTClient
from PromptBuilder.GPTPromptBuilder import GPTPromptBuilder 
from ProblemSampler.APPSProblemSampler import APPSProblemSampler
from utils import mkdir_override
import logging 
import logging.config
import asyncio
import json
import pathlib

async def request(semaphone, code_list, idx, client, **kwargs):
    async with semaphone:
        code_list[idx] = await client.request(**kwargs)

if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    client = GPTClient()
    sampler = APPSProblemSampler()
    builder = GPTPromptBuilder()

    save_dir = 'gpt_apps_code/'
    mkdir_override(save_dir)
    num_samples = 20
    num_workers = 8
    num_problems = 5

    for data in sampler.sample_from_head(num_problems):
        semaphone = asyncio.Semaphore(num_workers)
        async def batch_tasks():
            tasks = []
            code_list = [None] * num_samples
            for i in range(num_samples):
                task = asyncio.create_task(
                    request(
                        semaphone      = semaphone,
                        code_list      = code_list,
                        idx            = i,
                        client         = client,
                        task_name      = f'gpt_{data.problem_id}_{i}', 
                        model_name     = 'gpt-3.5-turbo-0301',
                        question       = data.question,
                        starter_code   = data.starter_code, 
                        save_dir       = None,
                        prompt_builder = builder
                    )
                )
                tasks.append(task)
            for task in tasks:
                await task
            with open(pathlib.Path(save_dir, f'gpt_{data.problem_id}.json'), 'w') as f:
                f.write(json.dumps(code_list))
        asyncio.run(batch_tasks())

