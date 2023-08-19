from abc import ABC, abstractmethod
from dataclasses import dataclass

class ProblemData(ABC):
    '''
    A piece of problem data.
    '''
    

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
