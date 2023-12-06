from abc import ABC, abstractmethod
import logging
import logging.config
import traceback

from Action import Action, ProgramAgentAction
from Observation import Observation, ProgramAgentObservation
from Strategy.Strategy import Strategy
from Task import Task, ProgramTask

from GPTClient import GPTClient
from Evaluator import Evaluator, sample_functions, eval_sampled_functions, eval_full_code
from ProblemSampler.ProblemSampler import ProblemData
from Tracer import get_sorted_funcs, trace_code
from utils import extract_imports, collect_counterexample, prepare_for_submit
from Config import CONFIG 

# Do action and change state according to Strategy. 
class Agent(ABC):

    @abstractmethod
    def execute(self, task: Task, action: Action):
        pass

# Program generation agent. 
class ProgramAgent(Agent):

    def __init__(self):
        self.logger = logging.getLogger('ProgramAgent')

    # Create and submit task in parallel
    async def dispatch(self,
                       task_name: str,
                       problem_data: ProblemData,
                       save_dir: str,
                       client: GPTClient,
                       model_name: str,
                       evaluator: Evaluator,
                       strategy: Strategy,
                       seed: int = CONFIG.seed):

        task = ProgramTask(task_name_prefix = task_name,
                           save_dir         = save_dir,
                           problem_data     = problem_data,
                           client           = client,
                           model_name       = model_name,
                           evaluator        = evaluator,
                           seed             = seed,
                           task_name        = task_name)
        await self.main_loop(task, strategy)

    # Observe and execute actions until the task is done
    async def main_loop(self, task: ProgramTask, strategy: Strategy):
        await self.execute(task, strategy.initial_actions)
        while task.running:
            obs = await self.observe(task)
            actions = await strategy.step(obs)
            await self.execute(task, actions)

    async def observe(self, task: ProgramTask):
        obs = ProgramAgentObservation(
            early_stop          = (task.evaluator.score == task.max_score),
            error_raised        = (task.error is not None)
        )
        task.error = None
        return obs

    async def execute(self, task: ProgramTask, actions: list[ProgramAgentAction]):
        for action in actions:
            assert isinstance(action, ProgramAgentAction)
            try:
                await action.execute(task)
            except Exception as err:
                traceback.print_exc()
                task.error = err
                break

