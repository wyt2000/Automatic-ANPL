from .Evaluator import Evaluator
from copy import deepcopy
from typing import List, Tuple

__all__ = ['MaxPassEvaluator']

class MaxPassEvaluator(Evaluator):
    # Trivial policy, just choose the program passed the most test cases.
    def __init__(self):
        self._final_submit = ['', []]
        self._best_result = ['', []]

    def update(self, program: str, asserts: List[str], passed_asserts: List[str]):
        if len(passed_asserts) >= len(self._best_result[1]):
            self._best_result = [program, passed_asserts]

    def restart(self):
        if len(self._best_result[1]) >= len(self._final_submit[1]):
            self._final_submit = deepcopy(self._best_result)
        self._best_result = ['', []]

    @property
    def best_result(self) -> Tuple[str, List[str]]:
        return self._best_result

    @property
    def final_submit(self) -> Tuple[str, List[str]]:
        return self._final_submit

    @property
    def score(self) -> int:
        return len(self.best_result[1])