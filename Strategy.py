from abc import ABC, abstractmethod
import logging
import logging.config
from dataclasses import dataclass

import Action
from Observation import Observation, ProgramAgentObservation
from Config import CONFIG

# Internal State of the agent, specified by Strategy.
class State(ABC):
    pass

# Give action by State and Observation
class Strategy(ABC):

    @property
    @abstractmethod
    def initial_actions(self) -> list[Action.Action]:
        pass
    
    @abstractmethod
    async def step(self, obs: Observation) -> Action.Action:
        pass

# Generation and self-debug in fixed times.
class SelfDebugStrategy(Strategy):

    # 3-level inner state in self-debug 
    @dataclass
    class ProgramState(State):
        restart_times        : int = 0
        solution_debug_times : int = 0
        program_debug_times  : int = 0

    def __init__(self,
                 max_restart_times        : int     = CONFIG.max_restart_times,
                 max_solution_debug_times : int     = CONFIG.max_solution_debug_times,
                 max_program_debug_times  : int     = CONFIG.max_program_debug_times,
                 num_generated_funcs      : int     = CONFIG.num_generated_funcs,
                 num_debugged_funcs       : int     = CONFIG.num_debugged_funcs,
                 num_pretests             : int     = CONFIG.num_pretests,
                 num_random_inputs        : int     = CONFIG.num_random_inputs,
                 num_verifiers            : int     = CONFIG.num_verifiers,
                 eval_max_attempts        : int     = CONFIG.eval_max_attempts,
                 eval_max_time            : float   = CONFIG.eval_max_time,
                 use_pretests             : bool    = CONFIG.use_pretests,
                 use_asserts              : bool    = CONFIG.use_asserts,
                 use_random_inputs        : bool    = CONFIG.use_random_inputs
                 ):

        self.max_restart_times        = max_restart_times
        self.max_solution_debug_times = max_solution_debug_times
        self.max_program_debug_times  = max_program_debug_times
        self.num_generated_funcs      = num_generated_funcs 
        self.num_debugged_funcs       = num_debugged_funcs
        self.num_pretests             = num_pretests
        self.num_random_inputs        = num_random_inputs
        self.num_verifiers            = num_verifiers
        self.eval_max_attempts        = eval_max_attempts
        self.eval_max_time            = eval_max_time
        self.use_pretests             = use_pretests
        self.use_random_inputs        = use_random_inputs

        self.state                    = self.ProgramState()
        self.logger                   = logging.getLogger('SelfDebugStrategy')

        # Generation from scratch and eval
        self.generation_actions       = []
        self.generation_actions.append(Action.GenerateSolution())
        self.generation_actions.append(Action.GenerateANPL())
        if use_asserts: self.generation_actions.append(Action.GenerateANPLWithAsserts())
        self.generation_actions.append(
            Action.GenerateFunction(num_completions=num_generated_funcs, use_asserts=use_asserts)
        )
        self.generation_actions.append(
            Action.EvalPretest(max_time=eval_max_time, max_attempts=eval_max_attempts)
        )

        
        # Generate tests or test generators + verifiers
        if use_pretests:
            self._initial_actions = [Action.GeneratePretest(num_completions=num_pretests)]
        else:
            self._initial_actions = [
                Action.GenerateRandomInput(num_random_inputs=num_random_inputs),
                Action.GenerateVerifier(num_verifiers=num_verifiers)
            ]
        self._initial_actions.extend([
            Action.Restart(),
            *self.generation_actions
        ])

        # Do final test and stop the process
        self.finish_actions   = [
            Action.Restart(),
            Action.EvalSystemTest(),
            Action.Finish()
        ]

    # Give up current result and start a new generation process
    def restart(self):
        self.state = self.ProgramState(self.state.restart_times + 1, 0, 0)
        return [
            Action.Restart(),
            *self.generation_actions
        ]
    
    # Generate pretest and enter the first generation process
    @property
    def initial_actions(self):
        return self._initial_actions    

    # Refresh state and give new action list according to current observation 
    async def step(self, obs: ProgramAgentObservation) -> list[Action.ProgramAgentAction]:
        state = self.state

        # Early stop
        if obs.early_stop:
            return self.finish_actions

        # Restart when error
        if obs.error_raised:
            return self.restart()

        # Debug in function-level
        if state.program_debug_times < self.max_program_debug_times:
            state.program_debug_times += 1
            return [
                Action.DebugFunction(num_completions=self.num_debugged_funcs),
                Action.EvalPretest(max_time=self.eval_max_time, max_attempts=self.eval_max_attempts)
            ]

        # Debug in solution-level
        if state.solution_debug_times < self.max_solution_debug_times:
            state.program_debug_times = 0
            state.solution_debug_times += 1
            return [
                Action.DebugSolution(),
                *self.generation_actions[1:]
            ]

        # Regenerate 
        if state.restart_times < self.max_restart_times:
            return self.restart()

        return self.finish_actions 

