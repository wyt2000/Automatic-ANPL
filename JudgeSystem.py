import traceback
import timeout_decorator

''' Judge Status Exception '''

class JudgeUnknownError(Exception):
    pass

class JudgeCompileError(Exception):
    pass

class JudgeRuntimeError(Exception):
    pass

class JudgeTimeLimitExceeded(Exception):
    pass

class JudgeWrongAnswer(Exception):
    pass

''' Judge Status Exception '''

''' Judge Status DataContainer'''

@dataclasses.dataclass
class JudgeStatusContainer:
    synthesizer_name: str = 'unknown'
    compile_errors : dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    time_limit_exceededs: dict[str, int] = dataclasses.field(default_factory=dict) 
    runtime_errors: dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    accepteds : dict[str, int] = dataclasses.field(default_factory=dict) 

''' Judge Status Container'''

class JudgeSystem:

    def __init__(self, synthesizer, time_limit=10):
        self.synthesizer = synthesizer
        self.time_limit = time_limit

    def compile(self, program, save_path, prog_name):
        try:
            code = self.synthesizer.synthesize(program, save_path, prog_name)
        except:
            traceback.print_exc()
            raise JudgeCompileError("Compile error during synthesizing!")
        try:
            module_path = os.path.splitext(code_path)[0]
            module = importlib.import_module(module_path.replace('/', '.'))
        except:
            traceback.print_exc()
            raise JudgeCompileError("Compile error during module loading, maybe the target program is invalid!")
        try:
            func = module.__getattribute__(data.func_name)
        except:
            traceback.print_exc()
            raise JudgeCompileError("Compile error during function getting, maybe the target function is missing!")
        return func
    
    def judge(self, func, specs, func_name):
        @timeout_decorator.timeout(time_limit)
        def timeout_func(inp):
            out = func(inp)
            return out
        for i, spec in enumerate(specs):
            inp, ans = spec
            judge_info = "on testcase {i}: {func_name}({repr(inp)}) = {repr(ans)}!"
            try:
                out = timeout_func(inp)
            except timeout_decorator.TimeoutError:
                raise JudgeTimeLimitExceeded(f"Time limit exceeded " + judge_info)
            except Exception:
                raise JudgeRuntimeError(f"Runtime error " + judge_info)
            if out != ans:
                raise JudgeWrongAnswer(f"Wrong answer " + judge_info)
        return True


