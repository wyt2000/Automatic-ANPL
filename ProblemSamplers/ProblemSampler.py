from abc import ABC, abstractmethod
from typing import Dict, List, Iterable 

__all__ = ['ProblemData', 'ProblemSampler']

class ProblemData(ABC):
    # A piece of problem data.
    def __init__(self, sample: Dict[str, str]):
        self.sample = sample

    @property
    @abstractmethod
    def problem_id(self) -> int:
        pass

    @property
    @abstractmethod
    def system_tests(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def question(self) -> str:
        pass

    @property
    @abstractmethod
    def entry_point(self) -> str:
        pass
    

class ProblemSampler(ABC):
    # Generate problem descriptions and I/O specs.

    @abstractmethod
    def sample(self, *args) -> Iterable[ProblemData]:
        # Sample problem from datasets or files.
        pass
