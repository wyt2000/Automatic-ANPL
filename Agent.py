# Problem solving agent, do action and change state according to Strategy 

from abc import ABC, abstractmethod
from enum import IntEnum, auto
from dataclasses import dataclass

from GPTClient import GPTClient
from Evaluator import eval_sampled_functions, Evaluator

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
    
    @abstractmethod
    def step(self, obs: Observation) -> Action:
        pass
    
# Do Action
class Agent(ABC):

    @abstractmethod
    def execute(self, action: Action):
        pass

#####################################################################################

class ProgramAgentAction(IntEnum):
    # Generation Stage
    GEN_PRETEST         = auto()
    GEN_SOLUTION        = auto() 
    GEN_ANPL            = auto()
    GEN_FUNCTION        = auto()
    IDLE                = auto()

    # Debug Stage
    DEBUG_FUNCTION      = auto() # include counterexample generation
    DEBUG_SOLUTION      = auto()
    FINISH              = auto()

@dataclass
class ProgramAgentObservation(Observation):
    all_pretests_passed : bool = False
    error_raised        : bool = False

class SelfDebugStrategy(Strategy):

    @dataclass
    class ProgramState(State):
        generation_stage     : ProgramAgentAction = ProgramAgentAction.GEN_PRETEST
        restart_times        : int = 0
        solution_debug_times : int = 0
        program_debug_times  : int = 0

    def __init__(self,
                 max_restart_times: int,
                 max_solution_debug_times: int,
                 max_program_debug_times: int):
        self.max_restart_times        = max_restart_times
        self.max_solution_debug_times = max_solution_debug_times
        self.max_program_debug_times  = max_program_debug_times
        self.ProgramState             = SelfDebugStrategy.ProgramState
        self.state                    = self.ProgramState()

    def restart(self):
        self.state = self.ProgramState(self.GenerationStage.NEW_SOLUTION, self.state.restart_times + 1, 0, 0)
        return ProgramAgentAction.IDLE

    def step(self, obs: ProgramAgentObservation) -> ProgramAgentAction:

        if obs.all_pretests_passed:
            return ProgramAgentAction.FINISH
        
        if obs.error_raised:
            return self.restart()

        state = self.state

        if (action := state.generation_stage) != ProgramAgentAction.IDLE:
            state.generation_stage += 1
            return action

        if state.program_debug_times < self.max_program_debug_times:
            state.program_debug_times += 1
            return ProgramAgentAction.DEBUG_FUNCTION

        if state.solution_debug_times < self.max_solution_debug_times:
            state.program_debug_times = 0
            state.solution_debug_times += 1
            return ProgramAgentAction.DEBUG_SOLUTION

        if state.restart_times < self.max_restart_times:
            return self.restart()

        return ProgramAgentAction.FINISH


class ProgramAgent(Agent):

    def __init__(self):
        pass
    
    def execute(self, action: ProgramAgentAction):
        match action:
            case ProgramAgentAction.IDLE:
                pass
            case ProgramAgentAction.GEN_PRETEST:
                pass
            case ProgramAgentAction.GEN_SOLUTION:
                pass
            case ProgramAgentAction.GEN_ANPL:
                pass
            case ProgramAgentAction.GEN_FUNCTION:
                pass
            case ProgramAgentAction.DEBUG_FUNCTION:
                pass
            case ProgramAgentAction.DEBUG_SOLUTION:
                pass
            case ProgramAgentAction.FINISH:
                pass
            case _:
                raise ValueError(f"Invalid Action: {action}")



    
