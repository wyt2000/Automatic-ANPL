import asyncio
import functools
import operator
import random
import time
from typing import Any, Iterator, List, Set
from .Evaluator import Evaluator 
from .ValidationEvaluator import ValidationEvaluator

from Utils.ProgramOperations import eval_program
from Utils.AsyncTimer import AsyncTimer

__all__ = [
    'sample_functions',
    'eval_full_code',
    'eval_sampled_functions',
    'validate_full_code',
    'validate_sampled_functions',
]

def product_to_tensor_idx(prod: int, dims: List[int], idx: int) -> List[int]:
    # Convert absolute index to list index
    # eg: If dims = [2,3,4], abs index 19 = list index [1, 1, 3]
    # 19 = 3 * 4 * (1) + 4 * (1) + 1 * (3)
    ans = []
    for dim in dims:
        prod //= dim
        ans.append(idx // prod)
        idx %= prod
    return ans


def sample_product(arrs: List[List[Any]], n: int, k: int) -> List[List[int]]:
    # Sample k from n Cartesian product indices.
    # eg: arrs = |2-elem-set| x |3-elem-set| x |4-elem-set|
    # If n = 12, k = 3, it equals to randomly choosing 3 list index tuples from the first 12 tuples of all 24 tuples.
    indices = random.sample(range(n), k)
    dims = [len(arr) for arr in arrs]
    prod = functools.reduce(operator.mul, dims, 1)
    return [
        product_to_tensor_idx(prod, dims, idx)
        for idx in indices
    ]

def compose_functions(indices_lists: List[List[str]],
                      func_candidates: List[List[str]]) -> Iterator[str]:
    # Compose sampled functions as a complete python code, yield as generator
    for indices in indices_lists:
        code = ''
        for i, j in enumerate(indices):
            code += func_candidates[i][j]
            code += '\n\n'
        yield code


def sample_functions(func_candidates: List[Set[str]],
                     max_attempts: int,
                     seed: int) -> [int, Iterator[str]]:
    # Sample functions to generate completed codes

    # Collect candidates as a 2D-list (func x candidate).
    func_candidates = [sorted(candidate) for candidate in func_candidates]
    num_candidates = functools.reduce(operator.mul, [len(s) for s in func_candidates], 1)

    # Randomly sample functions and compose.
    n_to_try = min(max_attempts, num_candidates)
    random.seed(seed)
    indices_lists = sample_product(func_candidates, num_candidates, n_to_try)
    code_generator = compose_functions(indices_lists, func_candidates)
    return n_to_try, code_generator

def eval_full_code(code: str, entry_point: str, asserts: List[str]):
    # Evaluate a single program by assert_str
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


async def eval_sampled_functions(code_generator: Iterator[str],
                                 entry_point: str,
                                 imports_prefix: str,
                                 asserts: List[str],
                                 evaluator: Evaluator,
                                 max_time: float):
    # Evaluate all programs in code_generator and update the results in evaluator
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


def validate_full_code(code: str, entry_point: str, validators: List[str], test_inputs: List[List[Any]]) -> int:
    # Validate a single program by the validator and tests
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


async def validate_sampled_functions(code_generator: Iterator[str],
                                     entry_point: str,
                                     imports_prefix: str,
                                     validators: List[str],
                                     test_inputs: List[List[Any]],
                                     evaluator: ValidationEvaluator,
                                     max_time: float):
    # Validate programs in code_generator by validators and tests, then update the results in evaluator
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


