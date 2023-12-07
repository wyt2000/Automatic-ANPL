from .ProgramAgentAction import ProgramAgentAction
from Task import ProgramTask

__all__ = ['Finish']

class Finish(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        task.running = False