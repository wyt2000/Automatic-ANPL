from abc import ABC, abstractmethod
from dataclasses import dataclass

from ProblemSampler.ProblemSampler import ProblemData
from GPTClient import GPTClient
from Evaluators import Evaluator
from Tracer import IOCollector
from typing import Any, Tuple, List, Set

# External state of task, specfied by Agent. 
class Task(ABC):
    pass

# Program generation task state. 
@dataclass
class ProgramTask(Task):
    task_name_prefix: str
    save_dir: str
    problem_data: ProblemData
    client: GPTClient
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

