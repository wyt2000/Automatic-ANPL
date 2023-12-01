from abc import ABC, abstractmethod
from dataclasses import dataclass

from ProblemSampler.ProblemSampler import ProblemData
from GPTClient import GPTClient
from Evaluator import Evaluator
from typing import Any

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
    restart_times: int              = 0
    task_name: str                  = None
    pretests: list[str]             = None
    random_inputs: list[Any]        = None
    verifiers: list[str]            = None
    solution: str                   = None 
    anpl_code: str                  = None 
    func_candidates: list[set[str]] = None
    imports_prefix: str             = None
    program: str                    = None
    counterexample: str | list[Any] = None
    error: Exception | None         = None
    running: bool                   = True 

