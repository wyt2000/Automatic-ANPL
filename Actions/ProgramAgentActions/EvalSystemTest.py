from .ProgramAgentAction import ProgramAgentAction
from Evaluators import eval_full_code
from GPTClient import GPTClient
from Tasks import ProgramTask
from utils import prepare_for_submit

__all__ = ['EvalSystemTest']

class EvalSystemTest(ProgramAgentAction):
    async def execute(self, task: ProgramTask):
        program      = task.evaluator.final_submit[0]
        program      = prepare_for_submit(program)
        system_tests = task.problem_data.system_tests
        self.logger.debug(f'{task.task_name}: System Testing...')
        passed_asserts = eval_full_code(
            code        = program,
            entry_point = task.problem_data.entry_point,
            asserts     = system_tests
        )
        success = (len(passed_asserts) == len(system_tests))
        if success:
            self.logger.debug(f'{task.task_name}: System Test passed! Successfully solve the problem!')
        else:
            self.logger.debug(f'{task.task_name}: System Test Failed! ')
            self.logger.debug(f'{task.task_name}: Best attempt passed {len(passed_asserts)} / {len(system_tests)} system tests!')
        GPTClient.save_one(program, task.save_dir, f'{task.task_name}_final_submit_{success}.py')