import random
from .ProblemSampler import ProblemData, ProblemSampler
from human_eval.data import read_problems # for humaneval 
from typing import Dict, List, Iterator

__all__ = ['HumanEvalProblemData', 'HumanEvalProblemSampler']

class HumanEvalProblemData(ProblemData):

    def __init__(self, sample: Dict[str, str]):
        self._problem_id = sample['task_id'].replace('/', '_')
        self._tests = []
        if 'test' in sample:
            self._tests = ['\n'.join([sample['test'], f"check({sample['entry_point']})"])]
        super().__init__(sample)

    @property
    def problem_id(self) -> int:
        return self._problem_id

    @property
    def system_tests(self) -> List[str]:
        return self._tests

    @property
    def question(self) -> str:
        return self.sample['prompt']

    @property
    def entry_point(self) -> str:
        return self.sample['entry_point']

    def __repr__(self):
        return f'{self.__class__.__name__}(problem_id={self.problem_id}, entry_point={self.entry_point})'

class HumanEvalProblemSampler(ProblemSampler):

    def __init__(self):
        self.problems = read_problems()
        self.valid_ids = [
            i for i in range(len(self.problems)) 
        ] 

    def sample(self, data_indices) -> Iterator[ProblemData]:
        for idx in data_indices: 
            yield HumanEvalProblemData(self.problems[f'HumanEval/{idx}'])

    def sample_from_head(self, num_problems) -> Iterator[ProblemData]:
        yield from self.sample(range(num_problems))

    def sample_randomly(self, num_problems, seed=42) -> Iterator[ProblemData]:
        random.seed(seed)
        yield from self.sample(random.sample(self.valid_ids, num_problems))

