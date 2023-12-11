from typing import List, Any

from Utils.ProgramOperations import eval_program

__all__ = [
    'collect_counterexample',
    'collect_counterexample_with_validator',
]

def collect_counterexample(asserts: List[str], program: str, entry_point: str) -> str:
    # Find the assert which makes the program fail
    for assert_stmt in asserts:
        try:
            _, exc = eval_program(
                code       = program,
                entry_name = entry_point,
                inputs     = assert_stmt
            ) 
        except Exception as err:
            exc = err
        if exc is not None:
            return assert_stmt 
    return None

def collect_counterexample_with_validator(code: str, entry_point: str, validators: List[str], test_inputs: List[List[Any]]) -> List[str, List[Any]]:
    for validator in validators:
        code_with_validator = '\n'.join([code, validator])
        for inputs in test_inputs:
            try:
                _, exc = eval_program(
                    code       = code_with_validator,
                    entry_name = f'validate_{entry_point}',
                    inputs     = inputs 
                ) 
            except Exception as err:
                exc = err
            if exc is not None:
                return validator, inputs
    return None, None 
