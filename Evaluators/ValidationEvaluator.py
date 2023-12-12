from .Evaluator import Evaluator

from copy import deepcopy
from typing import Tuple

__all__ = ['ValidationEvaluator']

class ValidationEvaluator(Evaluator):
    # Use |validators| x |passed input| as score.
    def __init__(self):
        self._final_submit = ['', 0]
        self._best_result = ['', 0]

    def update(self, program: str, score: int):
        if score >= self._best_result[1]:
            self._best_result = [program, score]

    def restart(self):
        if self._best_result[1] >= self.final_submit[1]:
            self._final_submit = deepcopy(self._best_result)
        self._best_result = ['', 0]

    @property
    def best_result(self) -> Tuple[str, int]:
        return self._best_result

    @property
    def final_submit(self) -> Tuple[str, int]:
        return self._final_submit

    @property
    def score(self) -> int:
        return self.best_result[1]