from .ProgramAgentAction import ProgramAgentAction
from Configs import CONFIG
from Tasks import ProgramTask

__all__ = ['GenerateOutputConstraint']

class GenerateOutputConstraint(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        output_constraints = await task.client.request_for_io_constraint(
            task_name           = task.task_name,
            function            = task.problem_data.question,
            io_type             = 'output',
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_output_constraint
            },
            num_completions     = 1
        )
        assert output_constraints, f'{task.task_name}: Couldn\'t generate output constraint!'
        task.output_constraint = output_constraints[0]