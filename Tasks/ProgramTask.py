from Evaluators import Evaluator
from LLMClients import LLMClient 
from ProblemSamplers import ProblemData
from Utils.Tracer import IOCollector
from .Task import Task

from dataclasses import dataclass
from typing import Any, List, Set, Tuple

__all__ = ['ProgramTask']

@dataclass
class ProgramTask(Task):
    # Program generation task state. 
    task_name_prefix: str
    save_dir: str
    problem_data: ProblemData
    client: LLMClient 
    model_name: str
    evaluator: Evaluator
    seed: int
    restart_times: int                          = 0
    task_name: str                              = None
    max_score: int                              = 0
    pretests: List[str]                         = None
    input_constraint: str                       = None
    output_constraint: str                      = None
    random_inputs: List[Any]                    = None
    validators: List[str]                       = None
    solution: str                               = None
    anpl_code: str                              = None
    func_candidates: List[Set[str]]             = None
    imports_prefix: str                         = None
    program: str                                = None
    counterexample: str | Tuple[str, List[Any]] = None
    func_traces: List[IOCollector]              = None
    error: Exception | None                     = None
    running: bool                               = True