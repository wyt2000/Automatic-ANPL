import faulthandler
faulthandler.enable()

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1' 

from GPTClient import GPTClient
from ProblemSampler.HumanEvalProblemSampler import HumanEvalProblemSampler, HumanEvalProblemData
from Prompter.Prompter import AbstractPrompter
from Prompter.ANPLPrompter import ANPLPrompter 
from Synthesizer.Synthesizer import AbstractSynthesizer 
from Synthesizer.ANPLSynthesizer import ANPLSynthesizer, eval_python, wrap_code, get_assert_str, eval_sampled_codes
from Tracer import trace_code
from utils import mkdir_override, mkdir_no_override, redirect_loggers, sample_product

import logging
import logging.config
import argparse
import asyncio
import json
import pathlib
import functools
import operator
import random
import ast
import tqdm
import traceback

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

question_prefix = "Complete the function:\n"
program_prefix = "from typing import *\n"

# Compose sampled functions as a complete python code, yield as generator
def generate_code(indices_sets: list[list[str]],
                  func_candidate_sets: list[list[str]]):
    for indices in indices_sets:
        code = ''
        for i, j in enumerate(indices):
            code += func_candidate_sets[i][j]
            code += '\n\n'
        yield code

async def solve_problem(task_name_prefix: str,
                        model_name: str,
                        client: GPTClient,
                        prompter: AbstractPrompter,
                        synthesizer: AbstractSynthesizer,
                        data: HumanEvalProblemData,
                        num_completions: int,
                        save_dir: str,
                        cache_dir: str,
                        delay_in_seconds: float = 1.0,
                        max_restart_times: int = 4,
                        max_solution_debug_times: int = 0,
                        max_program_debug_times: int = 2,
                        num_pretests: int = 100,
                        num_counterexamples: int = 16,
                        max_attempts: int = 100000,
                        max_time: float = 240,
                        seed = 42,
                        use_pretests_debug=False):

    logger.debug(f"{task_name_prefix}: start to solve the problem...")
    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    restart_times = 0
    solution_debug_times = 0
    program_debug_times = 0
    final_submit = None # The final program to test
    solution = None
    program = None
    anpl_code = None
    success = False
    score = 0
    all_attempts = {}
    best_attempt = ['', 0]
    question = question_prefix + data.prompt

    # Start a new generation of solution
    def restart():
        nonlocal restart_times
        nonlocal solution_debug_times, program_debug_times
        nonlocal solution, anpl_code, program, final_submit, score
        restart_times += 1
        logger.debug(f"{task_name_prefix}: restart {restart_times} times")
        final_submit = best_attempt[0] 
        solution_debug_times, program_debug_times = 0, 0
        solution, anpl_code, program = None, None, None
        all_attempts.clear()
        score = 0

    # Generate pretests
    pretests = await client.request_for_pretests(
        task_name         = task_name_prefix,
        completion_kwargs = {
            "model"       : model_name,
            "temperature" : 0.6,
            "n"           : num_pretests
        },
        question          = question,
        prompter          = prompter,
        save_dir          = save_dir,
        delay_in_seconds  = delay_in_seconds
    )
    pretests = list(set(pretests))
    # Try to solve the problem until reach max_restart_times
    while restart_times < max_restart_times:
        
        # New start
        if solution is None:
            # Generate new solution or use debugged solution
            task_name = f"{task_name_prefix}_{restart_times}"
            logger.debug(f"{task_name}: Generating new solution...")
            try:
                solution = await client.request_for_solutions(
                    task_name         = f"{task_name}",
                    completion_kwargs = {
                        "model"       : model_name,
                        "temperature" : 0.6,
                        "logit_bias"  : {755:-100}
                    },
                    question          = question,
                    prompter          = prompter,
                    save_dir          = save_dir,
                    delay_in_seconds  = delay_in_seconds
                )
            except Exception as err:
                logger.exception(err)
                restart()
                continue
            solution = solution[0]

        # Generate anpl code from solution
        if anpl_code is None:
            task_name = f"{task_name_prefix}_{restart_times}_{solution_debug_times}"
            logger.debug(f"{task_name}: Generating anpl code...")
            try:
                anpl_code = await client.request_for_codes(
                    task_name         = task_name,
                    completion_kwargs = {
                        "model"             : model_name,
                        "temperature"       : 0.2,
                        "presence_penalty"  : 0.1,
                    },
                    starter_code      = "",
                    func_name         = data.entry_point,
                    question          = question, 
                    solution          = solution,
                    suffix_name       = "anpl",
                    prompter          = prompter,
                    save_dir          = save_dir,
                    delay_in_seconds  = delay_in_seconds
                )
            except Exception as err:
                logger.exception(err)
                restart()
                continue

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
                        entry                   = data.entry_point,
                        question                = question,
                        asserts                 = pretests,
                        all_attempts            = all_attempts,
                        num_completions_list    = [num_completions]
                    )
                    score, program, _ = results[num_completions]
                    program = program_prefix + "\n" + program
            except Exception as err:
                logger.exception(err)
                restart()
                continue

        # Test the modified program 
        task_name = f"{task_name_prefix}_{restart_times}_{solution_debug_times}_{program_debug_times}"
        passed_asserts = []
        try:
            passed_asserts = eval_python(task_name, program, pretests)
        except Exception as err:
            pass
        logger.debug(f"{task_name}: Current attempt passed {len(passed_asserts)} / {len(pretests)} pretests!")

        # Save the program
        with open(pathlib.Path(save_dir, f"{task_name}.py"), "w") as f:
            f.write(program)
        
        # Update best_attempt
        if score >= best_attempt[1]:
            best_attempt = [program, score]

        # Generate counterexamples from question and program 
        if use_pretests_debug:
            counterexamples = pretests
        else:
            logger.debug(f"{task_name}: Generating counterexamples...")
            try:
                counterexamples = await client.request_for_counterexamples(
                    task_name         = task_name,
                    completion_kwargs = {
                        "model"       : model_name,
                        "temperature" : 0.6,
                        "n"           : num_counterexamples
                    },
                    question          = question,
                    program           = program,
                    prompter          = prompter,
                    save_dir          = save_dir,
                    delay_in_seconds  = delay_in_seconds
                )
            except Exception as err:
                logger.exception("{task_name}: Counterexample not found, restart!")
                restart()

        # Check if the program can pass the counterexample
        golden_io = None 
        for pretest in pretests:
            try:
                passed_asserts = eval_python(task_name, program, [pretest])
                if len(passed_asserts) == 0:
                    golden_io = pretest
                    break
            except Exception as err:
                pass

        # Restart if counterexample generation failed
        if golden_io is None:
            logger.debug("{task_name}: Counterexample not found, restart!")
            restart()
            continue

        # Save counterexample
        try:
            with open(pathlib.Path(save_dir, f'{task_name}.io'), 'w') as f:
                f.write(json.dumps(golden_io))
        except Exception as e:
            pass

        # High-level solution reflection if program_debug_times reach limit
        if program_debug_times == max_program_debug_times:
            # Restart to generate new solution if the limit of solution debug reached 
            if solution_debug_times == max_solution_debug_times:
                restart()
                continue
            solution_debug_times += 1
            program_debug_times = 0
            anpl_code, program = None, None
            task_name = f"{task_name_prefix}_{restart_times}_{solution_debug_times}"
            try:
                solution = await client.request_for_debugged_solution(
                    task_name         = f"{task_name}",
                    completion_kwargs = {
                        "model"       : model_name,
                        "temperature" : 0.6,
                        "logit_bias"  : {755:-100}
                    },
                    question          = question,
                    old_solution      = solution,
                    counterexample    = golden_io,
                    prompter          = prompter,
                    save_dir          = save_dir,
                    delay_in_seconds  = delay_in_seconds
                )
            except Exception as err:
                logger.exception(err)
                pass
            continue

        # Generate traces for each function under golden input
        func_names_sorted, func_codes, func_traces, exception = trace_code(program, golden_io, data.entry_point)
        if func_traces is None:
            logger.debug(f'{task_name}: Couldn\'t get function traces, restart!')
            restart()
            continue

        # Request for function debug in function dependency sequence
        logger.debug(f'{task_name}: Requesting for debugged function...')
        implementations = [{func_codes[name]} for name in func_names_sorted]
        with tqdm.tqdm(total=len(func_names_sorted)) as pbar:
            for i, func_name in enumerate(func_names_sorted):
                traces = func_traces.func_ios.get(func_name, [])
                try:
                    debugged_funcs = await client.request_for_debugged_function(
                        task_name         = task_name,
                        completion_kwargs = {
                            "model"             : model_name,
                            "temperature"       : 0.6, # high temperature to make more difference
                            "n"                 : num_completions // 2
                        },
                        question    = question,
                        solution    = solution,
                        program     = program,
                        func_name   = func_name,
                        holes       = set(func_names_sorted),
                        func_code   = func_codes[func_name],
                        func_traces = traces,
                        prompter    = prompter,
                        save_dir    = save_dir,
                        delay_in_seconds  = delay_in_seconds
                    )
                except Exception as err:
                    logger.exception(err)
                    continue
                # Filter syntax error funcs
                for func in debugged_funcs:
                    if len(func) == 0:
                        continue
                    try:
                        ast.parse(func)
                        implementations[i].add(func)
                    except Exception as e:
                        pass
                pbar.update(1)
        logger.debug(f'{task_name}: Request for debugged function done!')

        # TODO: Unify with ANPL code
        # Collect candidates as a 2D-list (func x candidate).
        func_candidate_sets = [list(candidate) for candidate in implementations]
        func_candidate_sets_dims = [len(s) for s in func_candidate_sets]
        num_candidates = functools.reduce(operator.mul, func_candidate_sets_dims, 1)

        # Randomly sample debugged functions.
        n_to_try = min(max_attempts // 2, num_candidates)
        random.seed(seed)
        indices_sets = sample_product(func_candidate_sets, num_candidates, n_to_try)
        code_generator = generate_code(indices_sets, func_candidate_sets)
        assert_str = get_assert_str(pretests)

        # Eval all sampled code to find best_attempt
        program_debug_times += 1
        task_name = f"{task_name_prefix}_{restart_times}_{solution_debug_times}_{program_debug_times}"
        try:
            log_path = pathlib.Path(save_dir, f"{task_name}.log")
            with redirect_loggers(log_path):
                score, program, _ = eval_sampled_codes(
                   task_name      = task_name,
                   code_generator = code_generator,
                   assert_str     = assert_str,
                   all_attempts   = all_attempts,
                   n_to_try       = n_to_try,
                   max_time       = max_time / 2
                )
                program = program_prefix + "\n" + program
        except Exception as err:
            logger.exception(err)
            restart()
            continue

        # Goto Test the modified program 

    # Eval system test
    logger.debug(f"{task_name_prefix}: Synthesizing done! System testing...")
    passed_asserts = []
    try:
        passed_asserts = eval_python(task_name_prefix, final_submit, data.test)
        if len(passed_asserts) != len(data.test):
            raise Exception("Wrong Answer!")
        with open(pathlib.Path(save_dir, f"{task_name_prefix}_accepted.py"), "w") as f:
            f.write(final_submit)
        logger.debug(f"{task_name_prefix}: Successfully solve the problem!")
        return True
    except Exception as err:
        logger.debug(err)
        logger.debug(f"{task_name_prefix}: System test Failed!")
        logger.debug(f"{task_name_prefix}: Passed {len(passed_asserts)} / {len(data.test)} system tests!")
        try:
            with open(pathlib.Path(save_dir, f"{task_name_prefix}_failed.py"), "w") as f:
                f.write(final_submit)
        except Exception:
            pass
        logger.debug(f"{task_name_prefix}: Can't solve the problem!")
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

    sampler = HumanEvalProblemSampler()
    client = GPTClient(cache_path=pathlib.Path(cache_prefix, "client_cache.json"))
    prompter = ANPLPrompter()
    synthesizer = ANPLSynthesizer()

    logger.debug(f"There are {args.num_problems} problems to be solved!") 

    max_retry_times = 3
    for data in sampler.sample_randomly(args.num_problems):
        retry_times = 0
        async def solve_problem_async():
            await solve_problem(
                task_name_prefix    = f"{data.task_id}",
                model_name          = "gpt-3.5-turbo-0301", 
                client              = client,
                prompter            = prompter,
                synthesizer         = synthesizer,
                data                = data,
                num_completions     = args.num_completions,
                save_dir            = str(save_dir),
                cache_dir           = str(cache_dir),
                use_pretests_debug  = True
            )
        try:
            save_dir = pathlib.Path(save_prefix, f"{data.task_id}")
            cache_dir = pathlib.Path(cache_prefix, f"{data.task_id}")
            asyncio.run(solve_problem_async())
        except Exception as err:
            logger.exception(err)
            if retry_times < max_retry_times:
                logger.exception("Raise unhandled error, Retry!")
                asyncio.run(solve_problem_async())
                retry_times += 1
        finally:
            client.cache.dump()

