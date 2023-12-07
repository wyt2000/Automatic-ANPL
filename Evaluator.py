# Evaluate the programs composed by different function implementations.

import functools
import operator
import random
import ast
from typing import Any, Iterator
from abc import ABC, abstractmethod 
import time
from copy import deepcopy
import asyncio

from Tracer import eval_program
from utils import AsyncTimer
from collections import defaultdict

###################################################################################

# Different policy to Record the best result.
class Evaluator(ABC):

    @abstractmethod
    def update(self, program: str, *args):
        pass

    @abstractmethod
    def restart(self):
        pass

    @property
    @abstractmethod
    def best_result(self) -> list[str, Any]:
        pass

    @property
    @abstractmethod
    def final_submit(self) -> list[str, Any]:
        pass

    @property
    @abstractmethod
    def score(self) -> int:
        pass

# Trivial policy, just choose the program passed the most test cases.
class MaxPassEvaluator(Evaluator):

    def __init__(self):
        self._final_submit = ['', []]
        self._best_result = ['', []]

    def update(self, program: str, asserts: list[str], passed_asserts: list[str]):
        if len(passed_asserts) >= len(self._best_result[1]):
            self._best_result = [program, passed_asserts]

    def restart(self):
        if len(self._best_result[1]) >= len(self._final_submit[1]):
            self._final_submit = deepcopy(self._best_result)
        self._best_result = ['', []]

    @property
    def best_result(self) -> list[str, list[str]]:
        return self._best_result

    @property
    def final_submit(self) -> list[str, list[str]]:
        return self._final_submit

    @property
    def score(self) -> int:
        return len(self.best_result[1])

# Use |validators| x |passed input| as score.
class ValidationEvaluator(Evaluator):

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
    def best_result(self) -> list[str, int]:
        return self._best_result

    @property
    def final_submit(self) -> list[str, int]:
        return self._final_submit

    @property
    def score(self) -> int:
        return self.best_result[1]

# Use the number of programs which output equals to current output as score.
class FuzzingEvaluator(Evaluator):

    def __init__(self):
        self.ios = defaultdict(defaultdict(int)) # dict[input, dict[output, cnt]]
        self.target_ios = defaultdict(set)       # dict[input, set[target_output]]
        self._best_result = ['', 0]
        self._final_submit = ['', 0]

    @staticmethod
    def h(self, ios: list[Any]):
        return hash(str(tuple(ios)))

    def update(self, program: str, mode: str, input_outputs: list[list[Any], list[Any]] = None):
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
    def best_result(self) -> list[str, int]:
        return self._best_result

    @property
    def final_submit(self) -> list[str, int]:
        return self._final_submit

    @property
    def score(self) -> int:
        return self.best_result[1]

# Use CodeT score to choose the best program with reasonable tests.
class CodetEvaluator(Evaluator):

    def __init__(self):
        self.all_attempts = {}

    def update(self, program: str, asserts: list[str], passed_asserts: list[str]):
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
    def best_result(self) -> list[str, list[str]]:
        if not self.all_attempts:
            return '' 
        return max(self.all_attempts.values())[2:]

    @property
    def final_submit(self) -> list[str, list[str]]:
        return self.best_result

    @property
    def score(self) -> int:
        return max(self.all_attempts.values())[0]

###################################################################################

# Convert absolute index to list index
# eg: If dims = [2,3,4], abs index 19 = list index [1, 1, 3]
# 19 = 3 * 4 * (1) + 4 * (1) + 1 * (3)
def product_to_tensor_idx(prod: int, dims: list[int], idx: int) -> list[int]:
    ans = []
    for dim in dims:
        prod //= dim
        ans.append(idx // prod)
        idx %= prod
    return ans

# Sample k from n Cartesian product indices.
# eg: arrs = |2-elem-set| x |3-elem-set| x |4-elem-set|
# If n = 12, k = 3, it equals to randomly choosing 3 list index tuples from the first 12 tuples of all 24 tuples.
def sample_product(arrs: list[list[Any]], n: int, k: int) -> list[list[int]]:
    indices = random.sample(range(n), k)
    dims = [len(arr) for arr in arrs]
    prod = functools.reduce(operator.mul, dims, 1)
    return [
        product_to_tensor_idx(prod, dims, idx)
        for idx in indices
    ]

# Compose sampled functions as a complete python code, yield as generator
def compose_functions(indices_lists: list[list[str]],
                      func_candidates: list[list[str]]) -> Iterator[str]:
    for indices in indices_lists:
        code = ''
        for i, j in enumerate(indices):
            code += func_candidates[i][j]
            code += '\n\n'
        yield code

# Sample functions to generate completed codes
def sample_functions(func_candidates: list[set[str]],
                     max_attempts: int,
                     seed: int) -> [int, Iterator[str]]:

    # Collect candidates as a 2D-list (func x candidate).
    func_candidates = [sorted(candidate) for candidate in func_candidates]
    num_candidates = functools.reduce(operator.mul, [len(s) for s in func_candidates], 1)

    # Randomly sample functions and compose.
    n_to_try = min(max_attempts, num_candidates)
    random.seed(seed)
    indices_lists = sample_product(func_candidates, num_candidates, n_to_try)
    code_generator = compose_functions(indices_lists, func_candidates)
    return n_to_try, code_generator

# Evaluate a single program by assert_str
def eval_full_code(code: str, entry_point: str, asserts: list[str]):
    passed_asserts = []
    for assert_stmt in asserts:
        try:
            _, exc = eval_program(
                code       = code,
                entry_name = entry_point,
                inputs     = assert_stmt 
            ) 
            if exc: continue
        except Exception as err:
            continue
        passed_asserts.append(assert_stmt)
    return passed_asserts

# Evaluate all programs in code_generator and update the results in evaluator
async def eval_sampled_functions(code_generator: Iterator[str],
                                 entry_point: str,
                                 imports_prefix: str,
                                 asserts: list[str],
                                 evaluator: Evaluator,
                                 max_time: float):
        
    max_time = int(max_time) * (10 ** 9)
    total_time = 0
    for code in code_generator:
        try:
            with AsyncTimer(time.time_ns()) as timer:
                code = '\n'.join([imports_prefix, code])
                passed_asserts = eval_full_code(code, entry_point, asserts)
                evaluator.update(code, asserts, passed_asserts)
            total_time += timer.time
            if total_time >= max_time:
                break
            await asyncio.sleep(0)
        except Exception as err:
            pass
    return evaluator.best_result

# Validate a single program by the validator and tests
def validate_full_code(code: str, entry_point: str, validators: list[str], test_inputs: list[list[Any]]) -> int:
    score = 0
    for validator in validators:
        code_with_validator = '\n'.join([code, validator])
        for inputs in test_inputs:
            try:
                _, exc = eval_program(
                    code       = code_with_validator,
                    entry_name = f'validate_{entry_point}',
                    inputs     = inputs 
                ) 
                if exc: continue
            except Exception as err:
                continue
            score += 1
    return score 

# Validate programs in code_generator by validators and tests, then update the results in evaluator
async def validate_sampled_functions(code_generator: Iterator[str],
                                     entry_point: str,
                                     imports_prefix: str,
                                     validators: list[str],
                                     test_inputs: list[list[Any]],
                                     evaluator: ValidationEvaluator,
                                     max_time: float):
    
    max_time = int(max_time) * (10 ** 9)
    total_time = 0
    for code in code_generator:
        try:
            with AsyncTimer(time.time_ns()) as timer:
                code = '\n'.join([imports_prefix, code])
                score = validate_full_code(code, entry_point, validators, test_inputs)
                evaluator.update(code, score)
            total_time += timer.time
            if total_time >= max_time:
                break
            await asyncio.sleep(0)
        except Exception as err:
            pass
    return evaluator.best_result


