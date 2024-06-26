from .ProgramAgentAction import ProgramAgentAction
from Tasks import ProgramTask
from Evaluators import eval_sampled_functions, sample_functions
from LLMClients.Collectors import collect_counterexample
from Utils.ProgramOperations import trace_code
from Utils.FileOperations import save_one

__all__ = ['EvalPretest']

class EvalPretest(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        n_to_try, code_generator = sample_functions(task.func_candidates, self.config['max_attempts'], task.seed)
        self.logger.debug(f'{task.task_name}: Evaluating {n_to_try} programs...')
        best_result = await eval_sampled_functions(
            code_generator = code_generator,
            entry_point    = task.problem_data.entry_point,
            imports_prefix = task.imports_prefix,
            asserts        = task.pretests,
            evaluator      = task.evaluator,
            max_time       = self.config['max_time']
        )
        self.logger.debug(f'{task.task_name}: Evaluating done!')
        self.logger.debug(f'{task.task_name}: Current best attempt passed {len(best_result[1])} / {task.max_score} pretests!')
        task.program = best_result[0]
        save_one(task.program, task.save_dir, f'{task.task_name}_program.py')
        task.counterexample = collect_counterexample(task.pretests, task.program, task.problem_data.entry_point)
        if task.counterexample is None: return
        _, _, task.func_traces, _ = trace_code(task.program, task.counterexample, task.problem_data.entry_point)
        if task.func_traces is None:
            raise Exception(f'{task.task_name}: Couldn\'t get function trace!')
        save_one(task.counterexample, task.save_dir, f'{task.task_name}.0.counterexample')