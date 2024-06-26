from abc import ABC, abstractmethod
from Tasks import Task

__all__ = ['Action']

# Request new solution or debug, specified by Agent.
class Action(ABC):
    
    @abstractmethod
    async def execute(self, task: Task):
        pass





