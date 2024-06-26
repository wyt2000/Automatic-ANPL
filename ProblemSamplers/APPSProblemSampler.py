import random
from .ProblemSampler import ProblemData, ProblemSampler

# for huggingface
import datasets
from datasets import load_dataset 

__all__ = ['APPSProblemData', 'APPSProblemSampler']

class APPSProblemData(ProblemData):
    
    def __repr__(self):
        return f'{self.__class__.__name__}(problem_id={self.problem_id}, url={self.url})'

class APPSProblemSampler(ProblemSampler):

    def __init__(self, path='codeparrot/apps', split='test', difficulties=['all']):
        datasets.config.DEFAULT_MAX_BATCH_SIZE = 10
        self.apps = load_dataset(path=path, split=split, difficulties=difficulties)
        self.valid_ids = [
                i for i in range(len(self.apps)) 
                if self.apps[i]["starter_code"] == '' # not support starter_code now.
        ] 
    def sample(self, data_indices):
        for idx in data_indices: 
            yield APPSProblemData(self.apps[idx])

    def sample_from_head(self, num_problems):
        yield from self.sample(range(num_problems))

    def sample_randomly(self, num_problems, seed=42):
        random.seed(seed)
        yield from self.sample(random.sample(self.valid_ids, num_problems))

if __name__ == '__main__':
    sampler = APPSProblemSampler(difficulties=['competition'])
    dataset = sampler.sample_randomly(10)
    for data in dataset:
        print(data)

