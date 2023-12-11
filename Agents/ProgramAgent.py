from Actions.ProgramAgentActions import ProgramAgentAction
from .Agent import Agent
from Configs import CONFIG
from Evaluators import Evaluator
from GPTClient import GPTClient
from Observations import ProgramAgentObservation
from ProblemSamplers import ProblemData
from Strategies import Strategy
from Tasks import ProgramTask

__all__ = ['ProgramAgent']

import logging
import traceback
from typing import List


class ProgramAgent(Agent):
    # Program generation agent. 
    def __init__(self):
        self.logger = logging.getLogger('ProgramAgent')

    async def dispatch(self,
                       task_name: str,
                       problem_data: ProblemData,
                       save_dir: str,
                       client: GPTClient,
                       model_name: str,
                       evaluator: Evaluator,
                       strategy: Strategy,
                       seed: int = CONFIG.seed):
        # Create and submit task in parallel

        task = ProgramTask(task_name_prefix = task_name,
                           save_dir         = save_dir,
                           problem_data     = problem_data,
                           client           = client,
                           model_name       = model_name,
                           evaluator        = evaluator,
                           seed             = seed,
                           task_name        = task_name)
        await self.main_loop(task, strategy)

    async def main_loop(self, task: ProgramTask, strategy: Strategy):
        # Observe and execute actions until the task is done
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

    async def execute(self, task: ProgramTask, actions: List[ProgramAgentAction]):
        for action in actions:
            try:
                await action.execute(task)
            except Exception as err:
                traceback.print_exc()
                task.error = err
                break