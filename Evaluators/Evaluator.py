# Evaluate the programs composed by different function implementations.

from typing import Tuple, Any
from abc import ABC, abstractmethod 
from typing import List

__all__ = ['Evaluator']

class Evaluator(ABC):
    # Different policy to Record the best result.
    @abstractmethod
    def update(self, program: str, *args):
        pass

    @abstractmethod
    def restart(self):
        pass

    @property
    @abstractmethod
    def best_result(self) -> Tuple[str, Any]:
        pass

    @property
    @abstractmethod
    def final_submit(self) -> Tuple[str, Any]:
        pass

    @property
    @abstractmethod
    def score(self) -> int:
        pass
