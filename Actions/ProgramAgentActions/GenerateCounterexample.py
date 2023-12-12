from .ProgramAgentAction import ProgramAgentAction
from Configs import CONFIG
from Tasks import ProgramTask

__all__ = ['GenerateCounterexample']

class GenerateCounterexample(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        counterexamples = await task.client.GenerateCounterexample(
            task_name         = task.task_name,
            question          = task.problem_data.question,
            program           = task.program,
            entry_point       = task.problem_data.entry_point,
            save_dir          = task.save_dir,
            completion_kwargs = {
                'model'       : task.model_name,
                **CONFIG.gen_counterexample
            },
            num_completions   = 1
        )
        assert counterexamples, f'{task.task_name}: Couldn\'t generate counterexample!'
        task.counterexample = counterexamples[0]