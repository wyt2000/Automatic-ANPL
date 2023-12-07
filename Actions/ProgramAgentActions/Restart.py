from .ProgramAgentAction import ProgramAgentAction
from Task import ProgramTask

__all__ = ['Restart']

class Restart(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        task.evaluator.restart()
        task.task_name = f'{task.task_name_prefix}_{task.restart_times}'
        task.restart_times += 1