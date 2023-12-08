from .ProgramAgentAction import ProgramAgentAction
from Config import CONFIG
from Tasks import ProgramTask

__all__ = ['GenerateANPL']

class GenerateANPL(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        anpl_codes = await task.client.request_for_anpl_codes(
            task_name           = task.task_name,
            save_dir            = task.save_dir,
            entry_point         = task.problem_data.entry_point,
            question            = task.problem_data.question,
            solution            = task.solution,
            completion_kwargs   = {
                'model'         : task.model_name,
                **CONFIG.gen_anpl
            },
            num_completions     = 1
        )
        assert anpl_codes, f'{task.task_name}: Couldn\'t generate anpl codes!'
        task.anpl_code = anpl_codes[0]