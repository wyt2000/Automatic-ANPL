# Evaluate the programs composed by different function implementations.

import functools
import operator
import random
import ast
from typing import Any, Iterator
from abc import ABC, abstractmethod 
import tqdm
import time
from copy import deepcopy

from Tracer import eval_program

###################################################################################

# Different policy to Record the best result.
class Evaluator(ABC):

    @abstractmethod
    def update(self, program: str, asserts: list[str], passed_asserts: list[str]):
        pass

    @abstractmethod
    def restart(self):
        pass

    @property
    @abstractmethod
    def best_result(self) -> list[str, list[str]]:
        pass

    @property
    @abstractmethod
    def final_submit(self) -> list[str, list[str]]:
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

# Use CodeT score to choose the best program with reasonable tests.
class CodetEvaluator(Evaluator):

    def __init__(self):
        self.all_attempts = {}

    def update(self, program: str, asserts: list[str], passed_asserts: list[str]):
        passed_asserts_hash = hash(tuple(passed_asserts))
        self.all_attempts[passed_asserts_hash] = [
            all_attempts.get(passed_asserts_hash, [0])[0] + len(passed_asserts), # CodeT
            len(passed_asserts),
            code,
            passed_asserts
        ]

    @property
    def best_result(self) -> str:
        if not all_attempts:
            return '' 
        return max(all_attempts.values())[2:]

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
        except Exception:
            continue
        passed_asserts.append(assert_stmt)
    return passed_asserts

# Evaluate all programs in code_generator and update the results in evaluator
def eval_sampled_functions(code_generator: Iterator[str],
                           n_to_try: int,
                           entry_point: str,
                           imports_prefix: str,
                           asserts: list[str],
                           evaluator: Evaluator,
                           max_time: int):

    start_time = time.time()
    with tqdm.tqdm(total=n_to_try) as pbar:
        for code in code_generator:
            if time.time() - start_time > max_time:
                break
            try:
                code = '\n'.join([imports_prefix, code])
                passed_asserts = eval_full_code(code, entry_point, asserts)
                evaluator.update(code, asserts, passed_asserts)
            finally:
                pbar.update(1)
    return evaluator.best_result


