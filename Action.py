from abc import ABC, abstractmethod
from typing import Any
from enum import Enum, auto
import logging

from Task import Task, ProgramTask
from GPTClient import GPTClient
from Evaluator import Evaluator, sample_functions, eval_sampled_functions, eval_full_code
from ProblemSampler.ProblemSampler import ProblemData
from Tracer import get_sorted_funcs, trace_code
from utils import extract_imports, collect_counterexample, prepare_for_submit
from Config import CONFIG 

# Request new solution or debug, specified by Agent.
class Action(ABC):
    
    @abstractmethod
    async def execute(self, task: Task):
        pass

# Program action with config dict 
class ProgramAgentAction(Action):

    def __init__(self, **config):
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.config = config

    def __repr__(self):
        return f'ProgramAgentAction({self.__class__.__name__}, {self.config})'

class GeneratePretest(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        pretests = await task.client.request_for_pretests(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_pretest
            },
            num_completions     = self.config['num_completions'] 
        )
        task.pretests = pretests.splitlines()

class GenerateRandomInput(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        try:
            task.random_inputs = await task.client.request_for_random_input( 
                task_name         = task.task_name,
                save_dir          = task.save_dir,
                func_name         = task.problem_data.entry_point,
                func_code         = task.problem_data.question,
                num_random_inputs = self.config['num_random_inputs'],
                completion_kwargs = {
                    'model'       : task.model_name,
                    **CONFIG.gen_random_input
                },
                num_completions   = 1
            )
        except Exception as err:
            self.logger.exception(err)

class GenerateSolution(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        solutions = await task.client.request_for_solutions(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_solution
            },
            num_completions     = 1
        )
        assert solutions, f'{task.task_name}: Couldn\'t generate solutions!'
        task.solution = solutions[0]

class GenerateANPL(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        anpl_codes = await task.client.request_for_anpl_codes(
            task_name           = task.task_name,
            save_dir            = task.save_dir,
            entry_point         = task.problem_data.entry_point,
            question            = task.problem_data.question,
            solution            = task.solution,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_anpl
            },
            num_completions     = 1
        )
        assert anpl_codes, f'{task.task_name}: Couldn\'t generate anpl codes!'
        task.anpl_code = anpl_codes[0]
    
class GenerateANPLWithAsserts(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        func_names_sorted, func_codes = get_sorted_funcs(task.anpl_code)
        entry_point = task.problem_data.entry_point
        anpl_with_assertions = await task.client.request_for_assertions(
            task_name           = task.task_name,
            save_dir            = task.save_dir,
            question            = task.problem_data.question,
            solution            = task.solution,
            anpl_code           = task.anpl_code,
            entry_point         = entry_point,
            func_code           = func_codes[entry_point],
            func_names          = set(func_names_sorted),
            completion_kwargs = {
                'model'       : task.model_name,
                **CONFIG.gen_anpl_with_asserts
            },
            num_completions     = 1
        )
        if anpl_with_assertions: task.anpl_code = anpl_with_assertions[0]

class GenerateFunction(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        func_names_sorted, func_codes = get_sorted_funcs(task.anpl_code)
        func_candidates = [set() for name in func_names_sorted]
        self.logger.debug(f'{task.task_name}: Synthesizing {len(func_names_sorted)} functions... ')
        for i, func_name in enumerate(func_names_sorted):
            generated_funcs = []
            try:
                generated_funcs = await task.client.request_for_function_completions( 
                    task_name         = f'{task.task_name}_{func_name}',
                    prefix            = '',
                    code              = task.anpl_code,
                    hole              = func_codes[func_name],
                    target            = func_name,
                    func_names        = set(func_names_sorted),
                    use_asserts       = self.config['use_asserts'],
                    completion_kwargs = {
                        "model"       : task.model_name,
                        **CONFIG.gen_function
                    },
                    num_completions   = self.config['num_completions']
                )
            except Exception as err:
                self.logger.exception(err)
            for func in generated_funcs:
                if len(func) == 0:
                    continue
                func_candidates[i].add(func) 
        self.logger.debug(f'{task.task_name}: Synthesizing done! ')
        task.func_candidates = func_candidates
        task.imports_prefix  = extract_imports(task.anpl_code)

class GenerateCounterexample(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        if self.config['use_pretests_debug']:
            task.counterexample = collect_counterexample(task.pretests, task.program, task.problem_data.entry_point)        
            GPTClient.save_one(task.counterexample, task.save_dir, f"{task.task_name}.0.counterexample")
            return
        counterexamples = await task.client.request_for_counterexamples(
            task_name         = task.task_name,
            question          = task.problem_data.question,
            program           = task.program,
            entry_point       = task.problem_data.entry_point,
            save_dir          = task.save_dir,
            completion_kwargs = {
                "model"       : task.model_name,
                **CONFIG.gen_counterexample
            },
            num_completions   = 1
        )
        assert counterexamples, f'{task.task_name}: Couldn\'t generate counterexample!'
        task.counterexample = counterexamples[0]

class DebugFunction(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        _, _, func_traces, _ = trace_code(task.program, task.counterexample, task.problem_data.entry_point)
        if func_traces is None:
            raise Exception(f'{task.task_name}: Couldn\'t get function trace!')
        func_names_sorted, func_codes = get_sorted_funcs(task.program)
        func_candidates = [{func_codes[name]} for name in func_names_sorted]
        self.logger.debug(f'{task.task_name}: Debugging {len(func_names_sorted)} functions... ')
        for i, func_name in enumerate(func_names_sorted):
            generated_funcs = []
            try:
                generated_funcs = await task.client.request_for_debugged_function( 
                    task_name         = f'{task.task_name}_{func_name}',
                    question          = task.problem_data.question,
                    solution          = task.solution,
                    program           = task.program,
                    target            = func_name,
                    func_names        = set(func_names_sorted),
                    func_code         = func_codes[func_name],
                    func_traces       = func_traces[func_name],
                    save_dir          = task.save_dir,
                    completion_kwargs = {
                        "model"       : task.model_name,
                        **CONFIG.debug_function
                    },
                    num_completions   = self.config['num_completions']
                )
            except Exception as err:
                self.logger.exception(err)
            for func in generated_funcs:
                if len(func) == 0:
                    continue
                func_candidates[i].add(func) 
        self.logger.debug(f'{task.task_name}: Debugging done! ')
        task.func_candidates = func_candidates
        task.imports_prefix  = extract_imports(task.program)

class DebugSolution(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        solutions = await task.client.request_for_debugged_solution(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            old_solution        = task.solution,
            counterexample      = task.counterexample,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.debug_solution
            },
            num_completions     = 1
        )
        assert solutions, f'{task.task_name}: Couldn\'t debug solutions!'
        task.solution = solutions[0]

class EvalPretest(ProgramAgentAction): 
    async def execute(self, task: ProgramTask):
        n_to_try, code_generator = sample_functions(task.func_candidates, self.config['max_attempts'], task.seed)
        self.logger.debug(f'{task.task_name}: Evaluating {n_to_try} programs...')
        best_result = await eval_sampled_functions(
            code_generator = code_generator,
            n_to_try       = n_to_try,
            entry_point    = task.problem_data.entry_point,
            imports_prefix = task.imports_prefix,
            asserts        = task.pretests,
            evaluator      = task.evaluator,
            max_time       = self.config['max_time']
        )
        self.logger.debug(f'{task.task_name}: Evaluating done!')
        self.logger.debug(f"{task.task_name}: Current best attempt passed {len(best_result[1])} / {len(task.pretests)} pretests!")
        task.program = best_result[0]
        GPTClient.save_one(task.program, task.save_dir, f"{task.task_name}_program.py")

class EvalSystemTest(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        program      = task.evaluator.final_submit[0]
        program      = prepare_for_submit(program)
        system_tests = task.problem_data.system_tests
        self.logger.debug(f'{task.task_name}: System Testing...')
        passed_asserts = eval_full_code(
            code        = program,
            entry_point = task.problem_data.entry_point,
            asserts     = system_tests
        )
        success = (len(passed_asserts) == len(system_tests))
        if success:
            self.logger.debug(f"{task.task_name}: System Test passed! Successfully solve the problem!")
        else:
            self.logger.debug(f"{task.task_name}: System Test Failed! ")
            self.logger.debug(f"{task.task_name}: Best attempt passed {len(passed_asserts)} / {len(system_tests)} system tests!")
        GPTClient.save_one(program, task.save_dir, f"{task.task_name}_final_submit_{success}.py")

class Restart(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        task.evaluator.restart()
        task.task_name = f"{task.task_name_prefix}_{task.restart_times}"
        task.restart_times += 1

class Finish(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        task.running = False


