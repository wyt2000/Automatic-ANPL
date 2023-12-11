from ..Collectors import collect_counterexample

__all__ = ['verify_counterexample']

def verify_counterexample(asserts: str, program: str, entry_point: str) -> bool:
    # Check if the program will raise an exception when tested by asserts
    return collect_counterexample(asserts.splitlines(), program, entry_point) is not None
