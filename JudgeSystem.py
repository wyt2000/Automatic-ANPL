import traceback
import timeout_decorator
import dataclasses
import os
import importlib

''' Judge Status Exception '''

class JudgeError(Exception):
    pass

class JudgeCompileError(JudgeError):
    pass

class JudgeRuntimeError(JudgeError):
    pass

class JudgeTimeLimitExceeded(JudgeError):
    pass

class JudgeWrongAnswer(JudgeError):
    pass

''' Judge Status Exception '''

''' Judge Status Container'''

@dataclasses.dataclass
class JudgeStatusContainer:
    synthesizer_name: str = 'unknown'
    judge_status: dict[str, list[tuple[str, int]]] = dataclasses.field(default_factory=dict)

''' Judge Status Container'''

class JudgeSystem:
    '''
    Evaluate whether target programs generated by the synthesizer satisfies I/O specs.
    Save judge status to calculate accuracy.
    '''

    def __init__(self, synthesizer, time_limit=10):
        '''
        :param synthesizer: synthesizer to be evaluated.
        :type synthesizer: Synthesizer
        
        :param time_limit: max time for program execuation.
        :type time_limit: float 
        '''
        self.synthesizer = synthesizer
        self.time_limit = time_limit
        self.judge_status_container = JudgeStatusContainer(synthesizer.name)

    def add_judge_status(self, status, data):
        '''
        Save judge status to `judge_status_container`

        :param status: status description.
        :type status: str 
        
        :param data: 
        :type data: ProgramData 
        '''
        judge_status = self.judge_status_container.judge_status
        if status not in judge_status:
            judge_status[status] = []
        judge_status[status].append((data.prog_name, data.num_snippets))

    def compile(self, program, save_path, data):
        '''
        DSL to target code by synthesizer, load target code from file and get function from it.

        :param program: the DSL.
        :type program: str

        :param save_path: path to save target code.
        :type save_path: str

        :param data: 
        :type data: ProgramData 

        :return: Python function can be executed immdiately.
        :rtype: function

        :raise JudgeCompileError:
        '''
        try:
            code = self.synthesizer.synthesize(program, save_path, data.prog_name)
        except:
            traceback.print_exc()
            raise JudgeCompileError("Compile error occurs during synthesizing!")
        try:
            module_path = os.path.splitext(save_path)[0]
            module = importlib.import_module(module_path.replace('/', '.'))
        except:
            traceback.print_exc()
            raise JudgeCompileError("Compile error occurs during module loading, maybe the target program is invalid!")
        try:
            func = module.__getattribute__(data.func_name)
        except:
            traceback.print_exc()
            raise JudgeCompileError("Compile error occurs during function getting, maybe the target function is missing!")
        return func
    
    #TODO: Support mutli-arg functions.
    def judge(self, func, specs, func_name):
        '''
        Feed func with inputs in specs and compare outputs with the answers in specs.

        :param func: The python function which has only one argument. 
        :type func: function 
       
        :param specs: I/O list.
        :type specs: list[tuple[str, str]]

        :param func_name:
        :type func_name: str

        :raise JudgeTimeLimitExceeded:
        :raise JudgeRuntimeError:
        :raise JudgeWrongAnswer:
        '''
        @timeout_decorator.timeout(self.time_limit)
        def timeout_func(inp):
            out = func(inp)
            return out
        for i, spec in enumerate(specs):
            inp, ans = spec
            judge_info = f"on testcase {i}, {func_name}({repr(inp)}) = {repr(ans)}!"
            try:
                out = timeout_func(inp)
            except timeout_decorator.TimeoutError:
                raise JudgeTimeLimitExceeded(f"Time limit exceeded " + judge_info)
            except Exception:
                raise JudgeRuntimeError(f"Runtime error " + judge_info)
            if out != ans:
                raise JudgeWrongAnswer(f"Wrong answer " + judge_info)


