import random
from .ProblemSampler import ProblemData, ProblemSampler

# for humaneval 
from human_eval.data import read_problems

class HumanEvalProblemData(ProblemData):

    def __init__(self, sample):
        self.task_id = sample['task_id'].replace('/', '_')
        self.test = []
        if 'test' in sample:
            self.test = [line.strip() for line in sample['test'].splitlines() if line.strip().startswith('assert')]
        super().__init__(sample)

    def __getattr__(self, name):
        if name == 'task_id':
            return self.task_id
        if name == 'test':
            return self.test
        return super().__getattr__(name)
    
    def __repr__(self):
        return f'{self.__class__.__name__}(task_id={self.task_id}, entry_point={self.entry_point})'

class HumanEvalProblemSampler(ProblemSampler):

    def __init__(self):
        self.problems = read_problems()
        self.valid_ids = [
            i for i in range(len(self.problems)) 
        ] 

    def sample(self, data_indices):
        for idx in data_indices: 
            yield HumanEvalProblemData(self.problems[f'HumanEval/{idx}'])

    def sample_from_head(self, num_problems):
        yield from self.sample(range(num_problems))

    def sample_randomly(self, num_problems, seed=42):
        random.seed(seed)
        yield from self.sample(random.sample(self.valid_ids, num_problems))

if __name__ == '__main__':
    sampler = HumanEvalProblemSampler()
    dataset = sampler.sample_randomly(10)
    for data in dataset:
        print(data)
        for t in data.test:
            print(t)

