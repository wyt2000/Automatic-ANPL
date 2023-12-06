from abc import ABC, abstractmethod

import Action
from Observation import Observation, ProgramAgentObservation

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

