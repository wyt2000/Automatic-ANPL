from abc import ABC, abstractmethod
from dataclasses import dataclass

# External Observation from GPT or Evaluator, specified by Agent.
class Observation(ABC):
    pass

# TODO: Add more obs
# Observation from Evaluator.
@dataclass
class ProgramAgentObservation(Observation):
    early_stop          : bool = False
    error_raised        : bool = False


