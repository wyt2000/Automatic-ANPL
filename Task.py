from abc import ABC, abstractmethod
from dataclasses import dataclass

from ProblemSampler.ProblemSampler import ProblemData
from GPTClient import GPTClient
from Evaluator import Evaluator

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
    solution: str                   = None 
    anpl_code: str                  = None 
    verifier: str                   = None
    func_candidates: list[set[str]] = None
    imports_prefix: str             = None
    program: str                    = None
    counterexample: str             = None
    error: Exception | None         = None
    running: bool                   = True 

