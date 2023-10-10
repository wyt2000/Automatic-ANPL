import os
os.environ['OPENBLAS_NUM_THREADS'] = '1' 

from GPTClient import GPTClient
from ProblemSampler.APPSProblemSampler import APPSProblemSampler, APPSProblemData
from Prompter.Prompter import AbstractPrompter
from Prompter.ANPLPrompter import ANPLPrompter 
from Synthesizer.Synthesizer import AbstractSynthesizer 
from Synthesizer.ANPLSynthesizer import ANPLSynthesizer 
from utils import mkdir_override, mkdir_no_override, redirect_loggers

import logging
import logging.config
import argparse
import asyncio
import json
import pathlib
import time

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

async def solve_problem(task_name_prefix: str,
                        model_name: str,
                        client: GPTClient,
                        prompter: AbstractPrompter,
                        synthesizer: AbstractSynthesizer,
                        data: APPSProblemData,
                        num_completions: int,
                        save_dir: str,
                        cache_dir: str,
                        delay_in_seconds: int = 1,
                        max_restart_times: int = 1):

    logger.debug(f"{task_name_prefix}: start to solve the problem...")
    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    restart_times = 0
    debug_solution_times = 0
    solution = None
    system_tests = json.loads(data.input_output)

    # Try to solve the problem until reach max_restart_times
    while restart_times < max_restart_times:
        task_name = f"{task_name_prefix}_{restart_times}_{debug_solution_times}"

        # Generate new solution or use debugged solution
        if solution is None:
            logger.debug(f"{task_name_prefix}_{restart_times}: Generating new solution...")
            solution = await client.request_for_solutions(
                task_name         = f"{task_name_prefix}_{restart_times}",
                completion_kwargs = {
                    "model"       : model_name,
                    "temperature" : 0.6,
                    "logit_bias"  : {755:-100}
                },
                question          = data.question,
                prompter          = prompter,
                save_dir          = save_dir,
                delay_in_seconds  = delay_in_seconds
            )
            solution = solution[0]

        # Generate anpl code from solution
        logger.debug(f"{task_name}: Generating anpl code...")
        anpl_code = await client.request_for_codes(
            task_name         = task_name,
            completion_kwargs = {
                "model"             : model_name,
                "temperature"       : 0.2,
                "presence_penalty"  : 0.1,
            },
            starter_code      = "",
            solution          = solution,
            suffix_name       = "anpl",
            prompter          = prompter,
            save_dir          = save_dir,
            delay_in_seconds  = delay_in_seconds
        )

        # Synthesize python code from anpl code
        logger.debug(f"{task_name}: Synthesizer python code...")
        program, success = None, False
        try:
            log_path = pathlib.Path(save_dir, f"{task_name}.log")
            with redirect_loggers(log_path):
                results = synthesizer.synthesize(
                    task_name               = task_name,
                    anpl_code               = anpl_code,
                    save_path_prefix        = pathlib.Path(save_dir, f"{task_name}"),
                    cache_path_prefix       = pathlib.Path(cache_dir, f"{task_name}"),
                    question                = data.question,
                    inputs                  = system_tests["inputs"],
                    outputs                 = system_tests["outputs"],
                    num_completions_list    = [num_completions]
                )
                program, success = results[0]
        except Exception as err:
            logger.exception(err)

        if success:
            logger.debug(f"{task_name}: Successfully solve the problem!")
            return True
        logger.debug(f"{task_name}: Debug Start!")
        
        restart_times += 1
    
    logger.debug(f"{task_name}: Can't solve the problem!")
    return False

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-k", "--num_completions", help="Number of function implementations for each code", type=int, default=4)
    args = argparser.parse_args()

    timestr = time.strftime("%m%d%H%M%S")
    save_prefix = f'anpl_apps_results_{timestr}'
    cache_prefix = f'anpl_apps_cache_{timestr}'
    mkdir_override(save_prefix)
    mkdir_no_override(cache_prefix)

    sampler = APPSProblemSampler(difficulties=['competition'])
    client = GPTClient(cache_path=pathlib.Path(cache_prefix, "client_cache.json"))
    prompter = ANPLPrompter()
    synthesizer = ANPLSynthesizer()

    logger.debug(f"There are {args.num_problems} problems to be solved!") 
    for data in sampler.sample_randomly(args.num_problems):
        try:
            save_dir = pathlib.Path(save_prefix, f"{data.problem_id}")
            cache_dir = pathlib.Path(cache_prefix, f"{data.problem_id}")
            asyncio.run(
                solve_problem(
                    task_name_prefix    = f"apps_{data.problem_id}",
                    model_name          = "gpt-3.5-turbo-0301", 
                    client              = client,
                    prompter            = prompter,
                    synthesizer         = synthesizer,
                    data                = data,
                    num_completions     = args.num_completions,
                    save_dir            = str(save_dir),
                    cache_dir           = str(cache_dir)
                )
            )
        except Exception as err:
            logger.exception(err)
        finally:
            client.cache.dump()

