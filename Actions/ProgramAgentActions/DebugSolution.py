from .ProgramAgentAction import ProgramAgentAction
from Configs import CONFIG
from Tasks import ProgramTask

__all__ = ['DebugSolution']

class DebugSolution(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        solutions = await task.client.DebugSolution(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            old_solution        = task.solution,
            counterexample      = task.counterexample,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.debug_solution
            },
            num_completions     = 1
        )
        assert solutions, f'{task.task_name}: Couldn\'t debug solutions!'
        task.solution = solutions[0]