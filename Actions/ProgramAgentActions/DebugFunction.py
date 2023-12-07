from .ProgramAgentAction import ProgramAgentAction
from Config import CONFIG
from Task import ProgramTask
from Tracer import get_sorted_funcs
from utils import extract_imports

__all__ = ['DebugFunction']

class DebugFunction(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        func_traces = task.func_traces
        func_names_sorted, func_codes = get_sorted_funcs(task.program)
        func_candidates = [{func_codes[name]} for name in func_names_sorted]
        self.logger.debug(f'{task.task_name}: Debugging {len(func_names_sorted)} functions... ')
        for i, func_name in enumerate(func_names_sorted):
            generated_funcs = []
            try:
                generated_funcs = await task.client.request_for_debugged_function(
                    task_name         = f'{task.task_name}_{func_name}',
                    question          = task.problem_data.question,
                    solution          = task.solution,
                    program           = task.program,
                    target            = func_name,
                    func_names        = set(func_names_sorted),
                    func_code         = func_codes[func_name],
                    func_traces       = func_traces[func_name],
                    save_dir          = task.save_dir,
                    completion_kwargs = {
                        "model"       : task.model_name,
                        **CONFIG.debug_function
                    },
                    num_completions   = self.config['num_completions']
                )
            except Exception as err:
                self.logger.exception(err)
            for func in generated_funcs:
                if len(func) == 0:
                    continue
                func_candidates[i].add(func)
        self.logger.debug(f'{task.task_name}: Debugging done! ')
        task.func_candidates = func_candidates
        task.imports_prefix  = extract_imports(task.program)