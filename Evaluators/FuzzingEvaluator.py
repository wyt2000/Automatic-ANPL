from .Evaluator import Evaluator
from collections import defaultdict
from copy import deepcopy
from typing import Any, List, Tuple

__all__ = ['FuzzingEvaluator']

class FuzzingEvaluator(Evaluator):
    # Use the number of programs which output equals to current output as score.
    def __init__(self):
        self.ios = defaultdict(defaultdict(int)) # dict[input, dict[output, cnt]]
        self.target_ios = defaultdict(set)       # dict[input, set[target_output]]
        self._best_result = ['', 0]
        self._final_submit = ['', 0]

    @staticmethod
    def h(ios: List[Any]):
        return hash(str(tuple(ios)))

    def update(self, program: str, mode: str, input_outputs: Tuple[List[Any], List[Any]] = None):
        '''
        Sample: Record the input x output count.
        Freeze: Get the max output.
        Evaluation: Calulate the score.
        '''
        if mode == 'Sample':
            for inputs, outputs in input_outputs:
                self.ios[self.h(inputs)][self.h(outputs)] += 1
        elif mode == 'Freeze':
            for inp, out_counter in self.ios.items():
                max_cnt = max(out_counter.values(), default=0)
                self.target_ios[inp] = set(out for out, cnt in out_counter.items() if cnt == max_cnt)
        elif mode == 'Evaluation':
            score = 0
            for inputs, outputs in input_outputs:
                if self.h(outputs) in self.target_ios[self.h(inputs)]:
                    score += 1
            if score >= self._best_result[1]:
                self._best_result = [program, score]
        else:
            raise TypeError(f'Invalid mode type {mode}!')

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