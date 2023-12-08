from dataclasses import dataclass
from typing import List

from .Strategy import Strategy, State
from Observations import ProgramAgentObservation
from Configs import CONFIG
import Actions.ProgramAgentActions as Action

__all__ = ['SelfDebugStrategy']

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
                 num_validators           : int     = CONFIG.num_validators,
                 eval_max_attempts        : int     = CONFIG.eval_max_attempts,
                 eval_max_time            : float   = CONFIG.eval_max_time,
                 use_pretests             : bool    = CONFIG.use_pretests,
                 use_asserts              : bool    = CONFIG.use_asserts,
                 use_random_inputs        : bool    = CONFIG.use_random_inputs
                 ):
        
        super().__init__()
        self.max_restart_times        = max_restart_times
        self.max_solution_debug_times = max_solution_debug_times
        self.max_program_debug_times  = max_program_debug_times
        self.num_generated_funcs      = num_generated_funcs 
        self.num_debugged_funcs       = num_debugged_funcs
        self.num_pretests             = num_pretests
        self.num_random_inputs        = num_random_inputs
        self.num_validators           = num_validators
        self.eval_max_attempts        = eval_max_attempts
        self.eval_max_time            = eval_max_time
        self.use_pretests             = use_pretests
        self.use_random_inputs        = use_random_inputs

        self.state                    = self.ProgramState()

        if self.use_pretests:
            self.eval_action          = Action.EvalPretest(max_time=eval_max_time, max_attempts=eval_max_attempts) 
        else:
            self.eval_action          = Action.Validate(max_time=eval_max_time, max_attempts=eval_max_attempts)

        # Generation from scratch and eval
        self.generation_actions       = []
        self.generation_actions.append(Action.GenerateSolution())
        self.generation_actions.append(Action.GenerateANPL())
        if use_asserts: self.generation_actions.append(Action.GenerateANPLWithAsserts())
        self.generation_actions.append(
            Action.GenerateFunction(num_completions=num_generated_funcs, use_asserts=use_asserts)
        )
        self.generation_actions.append(self.eval_action)
        
        # Generate tests or test generators + validators
        if use_pretests:
            self._initial_actions = [Action.GeneratePretest(num_completions=num_pretests)]
        else:
            self._initial_actions = [
                Action.GenerateInputConstraint(),
                Action.GenerateOutputConstraint(),
                Action.GenerateRandomInput(num_random_inputs=num_random_inputs),
                Action.GenerateValidator(num_validators=num_validators)
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

