from .ProgramAgentAction import ProgramAgentAction
from Configs import CONFIG
from Tasks import ProgramTask
from Tracer import get_sorted_funcs

__all__ = ['GenerateANPLWithAsserts']

class GenerateANPLWithAsserts(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        func_names_sorted, func_codes = get_sorted_funcs(task.anpl_code)
        entry_point = task.problem_data.entry_point
        anpl_with_assertions = await task.client.request_for_assertions(
            task_name           = task.task_name,
            save_dir            = task.save_dir,
            question            = task.problem_data.question,
            solution            = task.solution,
            anpl_code           = task.anpl_code,
            entry_point         = entry_point,
            func_code           = func_codes[entry_point],
            func_names          = set(func_names_sorted),
            completion_kwargs = {
                'model'       : task.model_name,
                **CONFIG.gen_anpl_with_asserts
            },
            num_completions     = 1
        )
        if anpl_with_assertions: task.anpl_code = anpl_with_assertions[0]