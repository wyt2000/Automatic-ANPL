from abc import ABC, abstractmethod
from dataclasses import dataclass

# External Observation from GPT or Evaluator, specified by Agent.
class Observation(ABC):
    pass

# TODO: Add more obs
# Observation from Evaluator.
@dataclass
class ProgramAgentObservation(Observation):
    all_pretests_passed : bool = False
    error_raised        : bool = False


