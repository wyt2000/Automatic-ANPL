from .ProgramAgentAction import ProgramAgentAction
from Configs import CONFIG
from Tasks import ProgramTask

__all__ = ['GeneratePretest']

class GeneratePretest(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        pretests = await task.client.GeneratePretest(
            task_name           = task.task_name,
            question            = task.problem_data.question,
            save_dir            = task.save_dir,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_pretest
            },
            num_completions     = self.config['num_completions']
        )
        task.pretests = pretests.splitlines()
        task.max_score = len(task.pretests)