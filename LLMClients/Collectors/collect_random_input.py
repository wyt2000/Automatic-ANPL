from typing import List, Any
from Configs import CONFIG
from Utils.ProgramOperations import eval_program

def collect_random_input(funcs: List[str], func_name: str, num_random_inputs: int) -> List[List[Any]]:
    # Generate random inputs by input generator `func_name`.
    random_inputs = []
    for func in funcs:
        for seed in range(CONFIG.seed, CONFIG.seed + num_random_inputs):
            try:
                ios, exc = eval_program(
                    code       = func,
                    entry_name = func_name,
                    inputs     = [seed],
                    with_trace = True,
                    func_names = [func_name]
                )
                if exc: raise exc
                random_inputs.append(ios[func_name][0].output) 
            except Exception as err:
                pass
    return random_inputs
