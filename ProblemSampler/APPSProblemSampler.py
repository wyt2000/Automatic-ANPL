import json
import random
from dataclasses import dataclass
from .ProblemSampler import ProblemData, ProblemSampler

# for huggingface
from datasets import load_dataset 

class APPSProblemData(ProblemData):
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
    
    def __repr__(self):
        return f'{self.__class__.__name__}(problem_id={self.problem_id}, url={self.url})'

class APPSProblemSampler(ProblemSampler):

    def __init__(self, path='codeparrot/apps', split='test', difficulties=['all']):
        self._apps = load_dataset(path=path, split=split, difficulties=difficulties)

    def sample(self, data_indices):
        for idx in data_indices: 
            yield APPSProblemData(self._apps[idx])

    def sample_from_head(self, num_problems):
        yield from self.sample(range(num_problems))

    def sample_randomly(self, num_problems):
        yield from self.sample(random.sample(range(len(self._apps)), num_problems))

if __name__ == '__main__':
    sampler = APPSProblemSampler()
    dataset = sampler.sample_from_head(10)
    for data in dataset:
        print(data)

