from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
import logging.config
import traceback

from Action import Action, ProgramAgentAction
from Observation import Observation, ProgramAgentObservation
from Strategy import Strategy

from GPTClient import GPTClient
from Evaluator import Evaluator, sample_functions, eval_sampled_functions, eval_full_code
from ProblemSampler.ProblemSampler import ProblemSampler, ProblemData
from Tracer import get_sorted_funcs, trace_code
from utils import extract_imports, collect_counterexample

# External state of task, specfied by Agent. 
class Task(ABC):
    pass

# Do action and change state according to Strategy. 
class Agent(ABC):

    @abstractmethod
    def execute(self, task: Task, action: Action):
        pass

# Program generation task state. 
@dataclass
class ProgramTask(Task):
    task_name_prefix: str
    save_dir: str
    problem_data: ProblemData
    client: GPTClient
    model_name: str
    evaluator: Evaluator 
    strategy: Strategy
    seed: int
    restart_times: int              = 0
    task_name: str                  = None
    pretests: list[str]             = None
    solution: str                   = None 
    anpl_code: str                  = None 
    func_candidates: list[set[str]] = None
    imports_prefix: str             = None
    program: str                    = None
    counterexample: str             = None
    error: Exception | None         = None
    running: bool                   = True 

# Program generation agent. 
class ProgramAgent(Agent):

    def __init__(self):
        self.logger = logging.getLogger('ProgramAgent')

    # Create and submit task in parallel
    async def dispatch(self,
                       task_name: str,
                       problem_data: ProblemData,
                       save_dir: str,
                       client: GPTClient,
                       model_name: str,
                       evaluator: Evaluator,
                       strategy: Strategy,
                       seed: int = 42):

        task = ProgramTask(task_name_prefix = task_name,
                           save_dir         = save_dir,
                           problem_data     = problem_data,
                           client           = client,
                           model_name       = model_name,
                           evaluator        = evaluator,
                           strategy         = strategy, 
                           seed             = seed,
                           task_name        = task_name)
        await self.main_loop(task)

    # Observe and execute actions until the task is done
    async def main_loop(self, task: ProgramTask):
        await self.execute(task, task.strategy.initial_actions)
        while task.running:
            obs = await self.observe(task)
            actions = await task.strategy.step(obs)
            await self.execute(task, actions)

    async def observe(self, task: ProgramTask):
        obs = ProgramAgentObservation(
            all_pretests_passed = (len(task.pretests) == len(task.evaluator.best_result[1])),
            error_raised        = (task.error is not None)
        )
        task.error = None
        return obs

    async def execute(self, task: ProgramTask, actions: list[ProgramAgentAction]):
        for action in actions:
            action_type = action.action_type.name
            if (func := getattr(self, f'execute_{action_type}')) is not None:
                try:
                    await func(task, **action.config)
                except Exception as err:
                    traceback.print_exc()
                    task.error = err
                    break
            else:
                raise ValueError(f'Undefined action type {action_type}!')

    async def execute_GEN_PRETEST(self, task: ProgramTask, num_completions: int):
        pretests = await task.client.request_for_pretests(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                'temperature'   : 0.6,
            },
            num_completions     = num_completions 
        )
        task.pretests = pretests.splitlines()
    
    async def execute_GEN_SOLUTION(self, task: ProgramTask):
        solutions = await task.client.request_for_solutions(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                'temperature'   : 0.6,
                'logit_bias'    : {755:-100}
            },
            num_completions     = 1
        )
        if not solutions: raise ValueError(f'{task.task_name}: Couldn\'t generate solutions!')
        task.solution = solutions[0]
    
    async def execute_GEN_ANPL(self, task: ProgramTask):
        anpl_codes = await task.client.request_for_anpl_codes(
            task_name           = task.task_name,
            save_dir            = task.save_dir,
            entry_point         = task.problem_data.entry_point,
            question            = task.problem_data.question,
            solution            = task.solution,
            completion_kwargs   = {
                "model"             : task.model_name,
                "temperature"       : 0.2,
                "presence_penalty"  : 0.1,
            },
            num_completions     = 1
        )
        if not anpl_codes: raise ValueError(f'{task.task_name}: Couldn\'t generate anpl codes!')
        task.anpl_code = anpl_codes[0]

    async def execute_GEN_FUNCTION(self, task: ProgramTask, num_completions: int):
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
                    completion_kwargs = {
                        "model"       : task.model_name,
                        "temperature" : 0.6, 
                    },
                    num_completions   = num_completions
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

    async def execute_GEN_COUNTEREXAMPLE(self, task: ProgramTask, use_pretests_debug: bool):
        if use_pretests_debug:
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
                "temperature" : 0.6
            },
            num_completions   = 1
        )
        if not counterexamples: raise ValueError(f'{task.task_name}: Couldn\'t generate counterexample!')
        task.counterexample = counterexamples[0]
    
    async def execute_DEBUG_FUNCTION(self, task: ProgramTask, num_completions):
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
                        "temperature" : 0.6, 
                    },
                    num_completions   = num_completions
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

    async def execute_DEBUG_SOLUTION(self, task: ProgramTask, **config):
        solutions = await task.client.request_for_debugged_solution(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            old_solution        = task.solution,
            counterexample      = task.counterexample,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                'temperature'   : 0.6,
                'logit_bias'    : {755:-100}
            },
            num_completions     = 1
        )
        if not solutions: raise ValueError(f'{task.task_name}: Couldn\'t debug solutions!')
        task.solution = solutions[0]
    
    async def execute_EVAL_PRETEST(self, task: ProgramTask, max_time: int, max_attempts: int):
        n_to_try, code_generator = sample_functions(task.func_candidates, max_attempts, task.seed)
        self.logger.debug(f'{task.task_name}: Evaluating {n_to_try} programs...')
        best_result = eval_sampled_functions(
            code_generator = code_generator,
            n_to_try       = n_to_try,
            entry_point    = task.problem_data.entry_point,
            imports_prefix = task.imports_prefix,
            asserts        = task.pretests,
            evaluator      = task.evaluator,
            max_time       = max_time
        )
        self.logger.debug(f'{task.task_name}: Evaluating done!')
        self.logger.debug(f"{task.task_name}: Current best attempt passed {len(best_result[1])} / {len(task.pretests)} pretests!")
        task.program = best_result[0]
        GPTClient.save_one(task.program, task.save_dir, f"{task.task_name}_program.py")
    
    async def execute_EVAL_SYSTEM_TEST(self, task: ProgramTask):
        program      = task.evaluator.final_submit[0]
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

    async def execute_RESTART(self, task: ProgramTask):
        task.evaluator.restart()
        task.task_name = f"{task.task_name_prefix}_{task.restart_times}"
        task.restart_times += 1

    async def execute_FINISH(self, task: ProgramTask):
        task.running = False

