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

    def __getattr__(self, name):
        if (attr := self.sample.get(name)) is not None:
            return attr
        raise AttributeError(f"{self.__class__.__name__} object has no attribute {name}") 


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
