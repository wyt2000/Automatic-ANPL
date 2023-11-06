from abc import ABC, abstractmethod
from dataclasses import dataclass

class ProblemData(ABC):
    '''
    A piece of problem data.
    '''
    def __init__(self, sample):
        '''
        :param sample: apps data.
        :type sample: dict[str, str]
        '''
        self.sample = sample

    @property
    @abstractmethod
    def problem_id(self) -> int:
        pass

    @property
    @abstractmethod
    def system_tests(self) -> list[str]:
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
    '''
    Generate problem descriptions and I/O specs.
    '''

    @abstractmethod
    def sample(self, *args):
        '''
        Sample problem from datasets or files.
        :return dataset: list of ProblemData
        '''
