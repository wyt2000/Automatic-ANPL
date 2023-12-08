from .ProgramAgentAction import ProgramAgentAction
from Evaluators import sample_functions, validate_sampled_functions
from GPTClient import GPTClient
from Tasks import ProgramTask
from Utils.Tracer import trace_code
from utils import collect_counterexample_with_validator

__all__ = ['Validate']

class Validate(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        # Generate codes
        n_to_try, code_generator = sample_functions(task.func_candidates, self.config['max_attempts'], task.seed)
        entry_point = task.problem_data.entry_point

        # Test by validators
        self.logger.debug(f'{task.task_name}: Validating {n_to_try} programs...')
        best_result = await validate_sampled_functions(
            code_generator = code_generator,
            entry_point    = entry_point,
            imports_prefix = task.imports_prefix,
            validators     = task.validators,
            test_inputs    = task.random_inputs,
            evaluator      = task.evaluator,
            max_time       = self.config['max_time']
        )
        self.logger.debug(f'{task.task_name}: Validating done!')
        self.logger.debug(f'{task.task_name}: Current best attempt got score {best_result[1]} / {task.max_score}!')
        task.program = best_result[0]
        GPTClient.save_one(task.program, task.save_dir, f'{task.task_name}_program.py')

        # Find one counterexample 
        validator, inputs = collect_counterexample_with_validator(
            code        = task.program,
            entry_point = entry_point,
            validators  = task.validators,
            test_inputs = task.random_inputs
        )
        if validator is None: return

        # Get traces
        _, _, func_traces, exc = trace_code(
            code        = '\n'.join([task.program, validator]),
            inputs      = inputs,
            entry_name  = f'validate_{entry_point}'
        )
        if func_traces is None:
            raise Exception(f'{task.task_name}: Couldn\'t get function trace!')

        func_traces[entry_point].extend(func_traces[f'validate_{entry_point}'])
        task.func_traces = func_traces
        task.counterexample = [validator, inputs]
        GPTClient.save_one(task.counterexample[1], task.save_dir, f'{task.task_name}.0.counterexample')