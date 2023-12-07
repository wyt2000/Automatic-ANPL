from .ProgramAgentAction import ProgramAgentAction
from Config import CONFIG
from Task import ProgramTask

__all__ = ['GenerateRandomInput']

class GenerateRandomInput(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        try:
            task.random_inputs = await task.client.request_for_random_input(
                task_name         = task.task_name,
                save_dir          = task.save_dir,
                func_name         = task.problem_data.entry_point,
                func_code         = task.problem_data.question,
                constraint        = task.input_constraint,
                num_random_inputs = self.config['num_random_inputs'],
                completion_kwargs = {
                    'model'       : task.model_name,
                    **CONFIG.gen_random_input
                },
                num_completions   = 1
            )
        except Exception as err:
            self.logger.exception(err)
        assert task.random_inputs, f'{task.task_name}: Couldn\'t generate random inputs!'