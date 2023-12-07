from abc import ABC, abstractmethod
import logging
import logging.config

from Actions import Action 
from Observation import Observation 

__all__ = ['Strategy']

# Internal State of the agent, specified by Strategy.
class State(ABC):
    pass

# Give action by State and Observation
class Strategy(ABC):

    def __init__(self):
        self.logger = logging.getLogger(f'{self.__class__.__name__}')

    @property
    @abstractmethod
    def initial_actions(self) -> list[Action]:
        pass
    
    @abstractmethod
    async def step(self, obs: Observation) -> Action:
        pass

