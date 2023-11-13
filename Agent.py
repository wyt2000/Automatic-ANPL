# Problem solving agent, do action and change state according to Strategy 

from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Type
import logging
import logging.config
import traceback
import tqdm

from GPTClient import GPTClient
from Evaluator import Evaluator, sample_functions, eval_sampled_functions, eval_full_code
from ProblemSampler.ProblemSampler import ProblemSampler, ProblemData
from Tracer import get_sorted_funcs, trace_code
from utils import extract_imports, collect_counterexample

#####################################################################################

# Internal State of the agent, specified by Strategy.
class State:
    pass

# External Observation from GPT or Evaluator, specified by Agent.
class Observation:
    pass

# Request new solution or debug, specified by Agent.
class Action:
    pass

# Give action by State and Observation
class Strategy(ABC):

    @property
    @abstractmethod
    def initial_actions(self) -> list[Action]:
        pass
    
    @abstractmethod
    async def step(self, obs: Observation) -> Action:
        pass
    
# Do Action
class Agent(ABC):

    @abstractmethod
    def execute(self, action: Action):
        pass

#####################################################################################

class ProgramAgentActionType(Enum):
    # Generation Stage
    GEN_PRETEST         = auto()
    GEN_SOLUTION        = auto() 
    GEN_ANPL            = auto()
    GEN_FUNCTION        = auto()

    # Debug Stage
    GEN_COUNTEREXAMPLE  = auto()
    DEBUG_FUNCTION      = auto() 
    DEBUG_SOLUTION      = auto()

    # Evaluate Stage
    EVAL_PRETEST        = auto()
    EVAL_SYSTEM_TEST    = auto()

    # Utils
    RESTART             = auto()
    FINISH              = auto()

class ProgramAgentAction(Action):

    def __init__(self, action_type: str, config: dict[str, Any] = {}):
        self.action_type = getattr(ProgramAgentActionType, action_type)
        self.config = config

    def __repr__(self):
        return f'ProgramAgentAction({self.action_type}, {self.config})'

@dataclass
class ProgramAgentObservation(Observation):
    all_pretests_passed : bool = False
    error_raised        : bool = False

class SelfDebugStrategy(Strategy):

    @dataclass
    class ProgramState(State):
        restart_times        : int = 0
        solution_debug_times : int = 0
        program_debug_times  : int = 0

    def __init__(self,
                 max_restart_times: int = 3,
                 max_solution_debug_times: int = 0,
                 max_program_debug_times: int = 2,
                 num_generated_funcs: int = 16,
                 num_debugged_funcs: int = 8,
                 num_pretests: int = 100,
                 eval_max_attempts: int = 100000,
                 eval_max_time: float = 240,
                 use_pretests_debug: bool = True):

        self.max_restart_times        = max_restart_times
        self.max_solution_debug_times = max_solution_debug_times
        self.max_program_debug_times  = max_program_debug_times
        self.num_generated_funcs      = num_generated_funcs 
        self.num_debugged_funcs       = num_debugged_funcs
        self.num_pretests             = num_pretests
        self.eval_max_attempts        = eval_max_attempts
        self.eval_max_time            = eval_max_time
        self.use_pretests_debug       = use_pretests_debug

        self.ProgramState             = SelfDebugStrategy.ProgramState
        self.state                    = self.ProgramState()
        self.logger                   = logging.getLogger('SelfDebugStrategy')

        self.generation_actions       = [
            ProgramAgentAction('GEN_SOLUTION'),
            ProgramAgentAction('GEN_ANPL'),
            ProgramAgentAction('GEN_FUNCTION', {'num_completions': num_generated_funcs}),
            ProgramAgentAction('EVAL_PRETEST', {'max_time': eval_max_time, 'max_attempts': eval_max_attempts})
        ]
        self.finish_actions           = [
            ProgramAgentAction('EVAL_SYSTEM_TEST'),
            ProgramAgentAction('FINISH')
        ]

    def restart(self):
        self.state = self.ProgramState(self.state.restart_times + 1, 0, 0)
        return [
            ProgramAgentAction('RESTART'),
            *self.generation_actions
        ]
    
    @property
    def initial_actions(self):
        return [
            ProgramAgentAction('GEN_PRETEST', {'num_completions': self.num_pretests}),
            ProgramAgentAction('RESTART'),
            *self.generation_actions
        ]
    
    # Maybe request for another LLM, so it should be async
    async def step(self, obs: ProgramAgentObservation) -> list[ProgramAgentAction]:
        state = self.state

        if obs.all_pretests_passed:
            return self.finish_actions

        if obs.error_raised:
            return self.restart()

        if state.program_debug_times < self.max_program_debug_times:
            state.program_debug_times += 1
            return [
                ProgramAgentAction('GEN_COUNTEREXAMPLE', {'use_pretests_debug': self.use_pretests_debug}),
                ProgramAgentAction('DEBUG_FUNCTION', {'num_completions': self.num_debugged_funcs}),
                ProgramAgentAction('EVAL_PRETEST', {'max_time': self.eval_max_time, 'max_attempts': self.eval_max_attempts})
            ]

        if state.solution_debug_times < self.max_solution_debug_times:
            state.program_debug_times = 0
            state.solution_debug_times += 1
            return [
                ProgramAgentAction('GEN_COUNTEREXAMPLE', {'use_pretests_debug': self.use_pretests_debug}),
                ProgramAgentAction('DEBUG_SOLUTION'),
                *self.generation_actions[1:]
            ]

        if state.restart_times < self.max_restart_times:
            return self.restart()

        return self.finish_actions 

@dataclass
class Task:
    task_name_prefix: str
    save_dir: str
    problem_data: ProblemData 
    evaluator: Evaluator 
    strategy: Strategy
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

class ProgramAgent(Agent):

    def __init__(self,
                 client: GPTClient,
                 model_name: str,
                 evaluator_type: Type[Evaluator],
                 strategy_type: Type[Strategy],
                 seed = 42):
        self.client = client
        self.model_name = model_name
        self.evaluator_type = evaluator_type
        self.strategy_type = strategy_type 
        self.seed = seed
        self.logger = logging.getLogger('ProgramAgent')

    async def dispatch(self, task_name: str, problem_data: ProblemData, save_dir: str, evaluator_config: dict = {}, strategy_config: dict = {}):
        task = Task(task_name_prefix = task_name,
                    save_dir         = save_dir,
                    problem_data     = problem_data,
                    evaluator        = self.evaluator_type(**evaluator_config),
                    strategy         = self.strategy_type(**strategy_config),
                    task_name        = task_name)
        await self.main_loop(task)

    async def main_loop(self, task: Task):
        await self.execute(task, task.strategy.initial_actions)
        while task.running:
            obs = await self.observe(task)
            actions = await task.strategy.step(obs)
            await self.execute(task, actions)

    async def observe(self, task: Task):
        obs = ProgramAgentObservation(
            all_pretests_passed = (len(task.pretests) == len(task.evaluator.best_result[1])),
            error_raised        = (task.error is not None)
        )
        task.error = None
        return obs

    async def execute(self, task: Task, actions: list[ProgramAgentAction]):
        for action in actions:
            action_type = action.action_type.name
            if (func := getattr(self, f'execute_{action_type}')) is not None:
                try:
                    await func(task, **action.config)
                except Exception as err:
                    traceback.print_exc()
                    task.error = err
            else:
                raise ValueError(f'Undefined action type {action_type}!')

    async def execute_GEN_PRETEST(self, task: Task, num_completions: int):
        pretests = await self.client.request_for_pretests(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : self.model_name,
                'temperature'   : 0.6,
            },
            num_completions     = num_completions 
        )
        task.pretests = pretests.splitlines()
    
    async def execute_GEN_SOLUTION(self, task: Task):
        solutions = await self.client.request_for_solutions(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : self.model_name,
                'temperature'   : 0.6,
                'logit_bias'    : {755:-100}
            },
            num_completions     = 1
        )
        if not solutions: raise ValueError(f'{task.task_name}: Couldn\'t generate solutions!')
        task.solution = solutions[0]
    
    async def execute_GEN_ANPL(self, task: Task):
        anpl_codes = await self.client.request_for_anpl_codes(
            task_name           = task.task_name,
            save_dir            = task.save_dir,
            entry_point         = task.problem_data.entry_point,
            question            = task.problem_data.question,
            solution            = task.solution,
            completion_kwargs   = {
                "model"             : self.model_name,
                "temperature"       : 0.2,
                "presence_penalty"  : 0.1,
            },
            num_completions     = 1
        )
        if not anpl_codes: raise ValueError(f'{task.task_name}: Couldn\'t generate anpl codes!')
        task.anpl_code = anpl_codes[0]

    async def execute_GEN_FUNCTION(self, task: Task, num_completions: int):
        func_names_sorted, func_codes = get_sorted_funcs(task.anpl_code)
        func_candidates = [set() for name in func_names_sorted]
        self.logger.debug(f'{task.task_name}: Synthesizing {len(func_names_sorted)} functions... ')
        with tqdm.tqdm(total=len(func_names_sorted)) as pbar:
            for i, func_name in enumerate(func_names_sorted):
                generated_funcs = []
                try:
                    generated_funcs = await self.client.request_for_function_completions( 
                        task_name         = f'{task.task_name}_{func_name}',
                        prefix            = '',
                        code              = task.anpl_code,
                        hole              = func_codes[func_name],
                        target            = func_name,
                        func_names        = set(func_names_sorted),
                        completion_kwargs = {
                            "model"       : self.model_name,
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
                pbar.update(1)   
        self.logger.debug(f'{task.task_name}: Synthesizing done! ')
        task.func_candidates = func_candidates
        task.imports_prefix  = extract_imports(task.anpl_code)

    async def execute_GEN_COUNTEREXAMPLE(self, task: Task, use_pretests_debug: bool):
        if use_pretests_debug:
            task.counterexample = collect_counterexample(task.pretests, task.program, task.problem_data.entry_point)        
            GPTClient.save_one(task.counterexample, task.save_dir, f"{task.task_name}.0.counterexample")
            return
        counterexamples = await self.client.request_for_counterexamples(
            task_name         = task.task_name,
            question          = task.problem_data.question,
            program           = task.program,
            entry_point       = task.problem_data.entry_point,
            save_dir          = task.save_dir,
            completion_kwargs = {
                "model"       : self.model_name,
                "temperature" : 0.6
            },
            num_completions   = 1
        )
        if not counterexamples: raise ValueError(f'{task.task_name}: Couldn\'t generate counterexample!')
        task.counterexample = counterexamples[0]
    
    async def execute_DEBUG_FUNCTION(self, task: Task, num_completions):
        _, _, func_traces, _ = trace_code(task.program, task.counterexample)
        func_names_sorted, func_codes = get_sorted_funcs(task.program)
        func_candidates = [{func_codes[name]} for name in func_names_sorted]
        self.logger.debug(f'{task.task_name}: Debugging {len(func_names_sorted)} functions... ')
        with tqdm.tqdm(total=len(func_names_sorted)) as pbar:
            for i, func_name in enumerate(func_names_sorted):
                generated_funcs = []
                try:
                    generated_funcs = await self.client.request_for_debugged_function( 
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
                            "model"       : self.model_name,
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
                pbar.update(1)   
        self.logger.debug(f'{task.task_name}: Debugging done! ')
        task.func_candidates = func_candidates
        task.imports_prefix  = extract_imports(task.program)

    async def execute_DEBUG_SOLUTION(self, task: Task, **config):
        solutions = await self.client.request_for_debugged_solution(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            old_solution        = task.solution,
            counterexample      = task.counterexample,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : self.model_name,
                'temperature'   : 0.6,
                'logit_bias'    : {755:-100}
            },
            num_completions     = 1
        )
        if not solutions: raise ValueError(f'{task.task_name}: Couldn\'t debug solutions!')
        task.solution = solutions[0]
    
    async def execute_EVAL_PRETEST(self, task: Task, max_time: int, max_attempts: int):
        n_to_try, code_generator = sample_functions(task.func_candidates, max_attempts, self.seed)
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
    
    async def execute_EVAL_SYSTEM_TEST(self, task: Task):
        program      = task.evaluator.best_result[0]
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

    async def execute_RESTART(self, task: Task):
        task.task_name = f"{task.task_name_prefix}_{task.restart_times}"
        task.restart_times += 1

    async def execute_FINISH(self, task: Task):
        task.running = False


    