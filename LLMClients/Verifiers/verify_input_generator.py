from Utils.ProgramOperations import eval_program
from Configs import CONFIG

__all__ = ['verify_input_generator']

def verify_input_generator(code: str, func_name: str) -> bool:
    # Check if the code has a callable input generator `func_name`.
    _, exc = eval_program(code, func_name, [CONFIG.seed])
    if exc:
        return False
    return True
