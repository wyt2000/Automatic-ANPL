import os
os.environ['OPENBLAS_NUM_THREADS'] = '1' 

from GPTClient import GPTClient
from ProblemSampler.APPSProblemSampler import APPSProblemSampler, APPSProblemData
from Prompter.Prompter import AbstractPrompter
from Prompter.ANPLPrompter import ANPLPrompter 
from Synthesizer.Synthesizer import AbstractSynthesizer 
from Synthesizer.ANPLSynthesizer import ANPLSynthesizer, eval_python, wrap_code
from Tracer import trace_code
from utils import mkdir_override, mkdir_no_override, redirect_loggers

import logging
import logging.config
import argparse
import asyncio
import json
import pathlib


logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

program_prefix = "from typing import *\n"

async def solve_problem(task_name_prefix: str,
                        model_name: str,
                        client: GPTClient,
                        prompter: AbstractPrompter,
                        synthesizer: AbstractSynthesizer,
                        data: APPSProblemData,
                        num_completions: int,
                        save_dir: str,
                        cache_dir: str,
                        delay_in_seconds: float = 1.0,
                        max_restart_times: int = 1,
                        max_solution_debug_times: int = 1,
                        num_counterexamples: int = 4,
                        max_attempts: int = 1000):

    logger.debug(f"{task_name_prefix}: start to solve the problem...")
    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    restart_times = 0
    solution_debug_times = 0
    program_debug_times = 0
    solution = None
    program = None
    success = False
    system_tests = json.loads(data.input_output)
    inputs, outputs = system_tests["inputs"], system_tests["outputs"]
    best_attempt = ["", []]

    # Start a new generation of solution
    def restart():
        restart_times += 1
        solution_debug_times, program_debug_times = 0, 0
        solution, program = None, None

    # Try to solve the problem until reach max_restart_times
    while restart_times < max_restart_times:
        
        # New start
        if solution is None:
            # Generate new solution or use debugged solution
            task_name = f"{task_name_prefix}_{restart_times}"
            logger.debug(f"{task_name}: Generating new solution...")
            solution = await client.request_for_solutions(
                task_name         = f"{task_name}",
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
            task_name = f"{task_name_prefix}_{restart_times}_{solution_debug_times}"
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

        # New program generation
        if program is None:
            # Synthesize python code from anpl code
            logger.debug(f"{task_name}: Synthesizing python code...")
            try:
                log_path = pathlib.Path(save_dir, f"{task_name}.log")
                with redirect_loggers(log_path):
                    results = synthesizer.synthesize(
                        task_name               = task_name,
                        anpl_code               = anpl_code,
                        save_path_prefix        = pathlib.Path(save_dir, f"{task_name}"),
                        cache_path_prefix       = pathlib.Path(cache_dir, f"{task_name}"),
                        question                = data.question,
                        inputs                  = inputs,
                        outputs                 = outputs,
                        num_completions_list    = [num_completions]
                    )
                    program, _ = results[num_completions]
                    program = program_prefix + "\n" + program
            except Exception as err:
                logger.exception(err)
                restart()
                continue

        # Test the modified program 
        task_name = f"{task_name_prefix}_{restart_times}_{solution_debug_times}_{program_debug_times}"
        passed_asserts = []
        try:
            passed_asserts = eval_python(task_name, program, (inputs, outputs))
        except Exception as err:
            logger.exception(err)
            pass

        # Update the best attempt
        if len(passed_asserts) >= len(best_attempt[1]):
            best_attempt = [program, passed_asserts]

        # Check if all system tests passed
        if len(passed_asserts) == len(inputs):
            success = True

        # Save the program
        with open(pathlib.Path(save_dir, f"{task_name}_{str(success)}.py"), "w") as f:
            f.write(program)

        # Exit if all system tests passed
        if success:
            logger.debug(f"{task_name}: Successfully solve the problem!")
            return True
        logger.debug(f"{task_name}: System Test Failed!")
        logger.debug(f"{task_name}: Best attempt passed {len(best_attempt[1])} / {len(inputs)} system tests!")

        # Restart to generate new solution if the limit of solution debug reached 
        if solution_debug_times == max_solution_debug_times:
            restart()
            continue

        # Generate counterexamples from question and program 
        logger.debug(f"{task_name}: Generating counterexamples...")
        counterexamples = await client.request_for_counterexamples(
            task_name         = task_name,
            completion_kwargs = {
                "model"       : model_name,
                "temperature" : 0.6,
                "n"           : num_counterexamples
            },
            question          = data.question,
            program           = program,
            prompter          = prompter,
            save_dir          = save_dir,
            delay_in_seconds  = delay_in_seconds
        )

        # Check if the program can pass the counterexample
        golden_io = [] 
        for inp, out in counterexamples:
            if not inp or not out: continue
            try:
                passed_asserts = eval_python(task_name, program, ([inp], [out]))
                if len(passed_asserts) == 0:
                    golden_io = [inp, out]
                    break
            except Exception as err:
                logger.exception(err)
                pass

        # Restart if counterexample generation failed
        if len(golden_io) == 0:
            logger.debug("{task_name}: Counterexample not found, restart!")
            restart()
            continue

        # Save counterexample
        with open(pathlib.Path(save_dir, f'{task_name}.io'), 'w') as f:
            f.write(json.dumps(golden_io))

        # Generate traces for each function under golden input
        func_names_sorted, func_codes, func_traces, exception = trace_code(program, golden_io[0])
        
        # Request for function debug in function dependency sequence
        implementation_sets = [set() for i in range(len(func_names_sorted))]
        for i, func_name in enumerate(func_names_sorted):
            traces = func_traces.func_ios[func_name]
            debugged_funcs = await client.request_for_debugged_function(
                task_name         = task_name,
                completion_kwargs = {
                    "model"             : model_name,
                    "temperature"       : 0.6, # high temperature to make more difference
                    "n"                 : num_completions 
                },
                solution    = solution,
                program     = program,
                func_name   = func_name,
                func_code   = func_codes[func_name],
                func_traces = traces,
                prompter    = prompter,
                save_dir    = save_dir,
                delay_in_seconds  = delay_in_seconds
            )
            implementation_sets[i].update([func for func in debugged_funcs if func])

        restart_times += 1
    
    logger.debug(f"{task_name}: Can't solve the problem!")
    return False

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, default=1)
    argparser.add_argument("-k", "--num_completions", help="Number of function implementations for each code", type=int, default=4)
    argparser.add_argument("-s", "--save_path", help="Path to save the results and logs", type=str, required=True)
    args = argparser.parse_args()

    save_prefix = args.save_path
    cache_prefix = f"{save_prefix}_cache"
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

