from .ProgramAgentAction import ProgramAgentAction
from Configs import CONFIG
from Tasks import ProgramTask

__all__ = ['GenerateSolution']

class GenerateSolution(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        solutions = await task.client.GenerateSolution(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_solution
            },
            num_completions     = 1
        )
        assert solutions, f'{task.task_name}: Couldn\'t generate solutions!'
        task.solution = solutions[0]