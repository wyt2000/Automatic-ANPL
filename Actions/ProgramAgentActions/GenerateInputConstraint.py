from .ProgramAgentAction import ProgramAgentAction
from Config import CONFIG
from Task import ProgramTask

__all__ = ['GenerateInputConstraint']

class GenerateInputConstraint(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        input_constraints = await task.client.request_for_io_constraint(
            task_name           = task.task_name,
            function            = task.problem_data.question,
            io_type             = 'input',
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_input_constraint
            },
            num_completions     = 1
        )
        assert input_constraints, f'{task.task_name}: Couldn\'t generate input constraint!'
        task.input_constraint = input_constraints[0]