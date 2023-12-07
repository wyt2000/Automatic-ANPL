from dataclasses import dataclass
from typing import List

from .Strategy import Strategy, State
from Observation import ProgramAgentObservation
from Config import CONFIG
import Actions.ProgramAgentActions as Action

__all__ = ['FuzzingStrategy']

# Rank programs by fuzzing tests.
class FuzzingStrategy(Strategy):
    '''
    STEP1: Generation inputs and programs.
    STEP2: Get outputs by executing the programs.
    STEP3: Rank programs by (inputs, outputs).
    '''

    # 3-level inner state in self-debug 
    @dataclass
    class ProgramState(State):
        evaluation           : bool = False
        restart_times        : int  = 0
        solution_debug_times : int  = 0
        program_debug_times  : int  = 0

    def __init__(self,
                 max_restart_times        : int     = CONFIG.max_restart_times,
                 max_solution_debug_times : int     = CONFIG.max_solution_debug_times,
                 max_program_debug_times  : int     = CONFIG.max_program_debug_times,
                 num_generated_funcs      : int     = CONFIG.num_generated_funcs,
                 num_debugged_funcs       : int     = CONFIG.num_debugged_funcs,
                 num_pretests             : int     = CONFIG.num_pretests,
                 num_random_inputs        : int     = CONFIG.num_random_inputs,
                 eval_max_attempts        : int     = CONFIG.eval_max_attempts,
                 eval_max_time            : float   = CONFIG.eval_max_time
                 ):
    
        super().__init__()
        self.max_restart_times        = max_restart_times
        self.max_solution_debug_times = max_solution_debug_times
        self.max_program_debug_times  = max_program_debug_times
        self.num_generated_funcs      = num_generated_funcs 
        self.num_debugged_funcs       = num_debugged_funcs
        self.num_pretests             = num_pretests
        self.num_random_inputs        = num_random_inputs
        self.eval_max_attempts        = eval_max_attempts
        self.eval_max_time            = eval_max_time

        self.state                    = self.ProgramState()

        self.eval_action          = Action.EvalPretest(max_time=eval_max_time, max_attempts=eval_max_attempts) 

        # Generation from scratch and eval
        self.generation_actions       = []
        self.generation_actions.append(Action.GenerateSolution())
        self.generation_actions.append(Action.GenerateANPL())
        self.generation_actions.append(
            Action.GenerateFunction(num_completions=num_generated_funcs, use_asserts=False)
        )
        self.generation_actions.append(self.eval_action)
        
        # Generate tests or test generators + validators
        self._initial_actions = [
            Action.GeneratePretest(num_completions=num_pretests),
            Action.GenerateInputConstraint(),
            Action.GenerateOutputConstraint(),
            Action.GenerateRandomInput(num_random_inputs=num_random_inputs),
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
    async def step(self, obs: ProgramAgentObservation) -> List[Action.ProgramAgentAction]:
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
                self.eval_action
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

