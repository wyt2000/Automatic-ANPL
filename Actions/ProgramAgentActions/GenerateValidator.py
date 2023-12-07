from .ProgramAgentAction import ProgramAgentAction
from Config import CONFIG
from Task import ProgramTask

__all__ = ['GenerateValidator']

class GenerateValidator(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        try:
            task.validators = await task.client.request_for_validator(
                task_name         = task.task_name,
                save_dir          = task.save_dir,
                func_name         = task.problem_data.entry_point,
                func_code         = task.problem_data.question,
                completion_kwargs = {
                    'model'       : task.model_name,
                    **CONFIG.gen_validator
                },
                num_completions   = self.config['num_validators']
            )
            task.max_score = len(task.random_inputs) * len(task.validators)
        except Exception as err:
            self.logger.exception(err)
        assert task.validators, f'{task.task_name}: Couldn\'t generate validators!'