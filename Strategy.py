from abc import ABC, abstractmethod
import logging
import logging.config
from dataclasses import dataclass

from Observation import Observation, ProgramAgentObservation
from Action import Action, ProgramAgentAction

# Internal State of the agent, specified by Strategy.
class State(ABC):
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

# Generation and self-debug in fixed times.
class SelfDebugStrategy(Strategy):

    # 3-level inner state in self-debug 
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

        self.state                    = self.ProgramState()
        self.logger                   = logging.getLogger('SelfDebugStrategy')

        # Generation from scratch and eval
        self.generation_actions       = [
            ProgramAgentAction('GEN_SOLUTION'),
            ProgramAgentAction('GEN_ANPL'),
            ProgramAgentAction('GEN_FUNCTION', {'num_completions': num_generated_funcs}),
            ProgramAgentAction('EVAL_PRETEST', {'max_time': eval_max_time, 'max_attempts': eval_max_attempts})
        ]

        # Do final test and stop the process
        self.finish_actions           = [
            ProgramAgentAction('RESTART'),
            ProgramAgentAction('EVAL_SYSTEM_TEST'),
            ProgramAgentAction('FINISH')
        ]

    # Give up current result and start a new generation process
    def restart(self):
        self.state = self.ProgramState(self.state.restart_times + 1, 0, 0)
        return [
            ProgramAgentAction('RESTART'),
            *self.generation_actions
        ]
    
    # Generate pretest and enter the first generation process
    @property
    def initial_actions(self):
        return [
            ProgramAgentAction('GEN_PRETEST', {'num_completions': self.num_pretests}),
            ProgramAgentAction('RESTART'),
            *self.generation_actions
        ]
    
    # Refresh state and give new action list according to current observation 
    async def step(self, obs: ProgramAgentObservation) -> list[ProgramAgentAction]:
        state = self.state

        # Early stop
        if obs.all_pretests_passed:
            return self.finish_actions

        # Restart when error
        if obs.error_raised:
            return self.restart()

        # Debug in function-level
        if state.program_debug_times < self.max_program_debug_times:
            state.program_debug_times += 1
            return [
                ProgramAgentAction('GEN_COUNTEREXAMPLE', {'use_pretests_debug': self.use_pretests_debug}),
                ProgramAgentAction('DEBUG_FUNCTION', {'num_completions': self.num_debugged_funcs}),
                ProgramAgentAction('EVAL_PRETEST', {'max_time': self.eval_max_time, 'max_attempts': self.eval_max_attempts})
            ]

        # Debug in solution-level
        if state.solution_debug_times < self.max_solution_debug_times:
            state.program_debug_times = 0
            state.solution_debug_times += 1
            return [
                ProgramAgentAction('GEN_COUNTEREXAMPLE', {'use_pretests_debug': self.use_pretests_debug}),
                ProgramAgentAction('DEBUG_SOLUTION'),
                *self.generation_actions[1:]
            ]

        # Regenerate 
        if state.restart_times < self.max_restart_times:
            return self.restart()

        return self.finish_actions 

