from .Evaluator import Evaluator
from typing import List, Tuple

__all__ = ['CodetEvaluator']

class CodetEvaluator(Evaluator):
    # Use CodeT score to choose the best program with reasonable tests.
    def __init__(self):
        self.all_attempts = {}

    def update(self, program: str, asserts: List[str], passed_asserts: List[str]):
        passed_asserts_hash = hash(tuple(passed_asserts))
        self.all_attempts[passed_asserts_hash] = [
            self.all_attempts.get(passed_asserts_hash, [0])[0] + len(passed_asserts), # CodeT
            len(passed_asserts),
            program,
            passed_asserts
        ]

    def restart(self):
        pass

    @property
    def best_result(self) -> Tuple[str, List[str]]:
        if not self.all_attempts:
            return ''
        return max(self.all_attempts.values())[2:]

    @property
    def final_submit(self) -> Tuple[str, List[str]]:
        return self.best_result

    @property
    def score(self) -> int:
        return max(self.all_attempts.values())[0]