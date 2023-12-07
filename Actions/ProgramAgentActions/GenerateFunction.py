from .ProgramAgentAction import ProgramAgentAction
from Config import CONFIG
from Task import ProgramTask
from Tracer import get_sorted_funcs
from utils import extract_imports

__all__ = ['GenerateFunction']

class GenerateFunction(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        func_names_sorted, func_codes = get_sorted_funcs(task.anpl_code)
        func_candidates = [set() for name in func_names_sorted]
        self.logger.debug(f'{task.task_name}: Synthesizing {len(func_names_sorted)} functions... ')
        for i, func_name in enumerate(func_names_sorted):
            generated_funcs = []
            try:
                generated_funcs = await task.client.request_for_function_completions(
                    task_name         = f'{task.task_name}_{func_name}',
                    prefix            = '',
                    code              = task.anpl_code,
                    hole              = func_codes[func_name],
                    target            = func_name,
                    func_names        = set(func_names_sorted),
                    use_asserts       = self.config['use_asserts'],
                    completion_kwargs = {
                        'model'       : task.model_name,
                        **CONFIG.gen_function
                    },
                    num_completions   = self.config['num_completions']
                )
            except Exception as err:
                self.logger.exception(err)
            for func in generated_funcs:
                if len(func) == 0:
                    continue
                func_candidates[i].add(func)
        self.logger.debug(f'{task.task_name}: Synthesizing done! ')
        task.func_candidates = func_candidates
        task.imports_prefix  = extract_imports(task.anpl_code)