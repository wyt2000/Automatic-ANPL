from abc import ABC, abstractmethod
from typing import Any
from enum import Enum, auto

# Request new solution or debug, specified by Agent.
class Action(ABC):
    pass

# Action to control the process of program generation and debug.
class ProgramAgentActionType(Enum):
    # Generation Stage
    GEN_PRETEST         = auto()
    GEN_SOLUTION        = auto() 
    GEN_ANPL            = auto()
    GEN_VERIFICATION    = auto()
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

# Wrapper of `ProgramAgentActionType` with config
class ProgramAgentAction(Action):

    def __init__(self, action_type: str, config: dict[str, Any] = {}):
        self.action_type = getattr(ProgramAgentActionType, action_type)
        self.config = config

    def __repr__(self):
        return f'ProgramAgentAction({self.action_type}, {self.config})'


