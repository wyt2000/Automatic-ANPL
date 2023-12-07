from .Observation import Observation
from dataclasses import dataclass

@dataclass
class ProgramAgentObservation(Observation):
    # Observation from Evaluator.
    early_stop          : bool = False
    error_raised        : bool = False