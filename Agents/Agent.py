from abc import ABC, abstractmethod

from Actions import Action
from Tasks import Task

__all__ = ['Agent']

class Agent(ABC):

    # Do action and change state according to Strategy. 
    @abstractmethod
    def execute(self, task: Task, action: Action):
        pass


