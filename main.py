import os
import pathlib
import importlib
import json
import dataclasses
import timeout_decorator
import traceback

from ProgramSampler import ProgramSampler 
from GPT2Code import GPT2Code 
from ANPLCompiler import ANPLCompiler
from ParselCompiler import ParselCompiler
from ParselPrompts import background as parsel_background
from ParselPrompts import pre_prompt as parsel_pre_prompt
from ParselPrompts import post_prompt as parsel_post_prompt
from ParselPrompts import extract_code as parsel_extract_code
from utils import mkdir_override

time_limit = 10

@dataclasses.dataclass
class CompileInfo:
    compiler_name : str = 'anpl'
    compile_errors : dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    time_limit_exceededs: dict[str, int] = dataclasses.field(default_factory=dict) 
    runtime_errors: dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    accepteds : dict[str, int] = dataclasses.field(default_factory=dict) 

def test_compiler(sampler, compiler, robot, model_name, prompt_dir, response_dir, result_dir, compile_info_path):
    try:
        mkdir_override(response_dir)
        mkdir_override(result_dir)
        compile_info = CompileInfo(compiler.name)

        for i, data in enumerate(sampler.dataset):
            try:
                task_name = f"{compiler.name}_{data.prog_name}"
                print(f'{task_name}: requesting for {model_name}...')
                response = robot.request(model_name,
                                         data.func_name,
                                         data.prompt, 
                                         os.path.join(response_dir, f"{task_name}.res"))
                print(f'{task_name} request for {model_name} done!, the response {compiler.name} code is:\n{response}')
                code_path = os.path.join(result_dir, f"{task_name}.py")
                try:
                    code = compiler.compile(data.prog_name, response, code_path)
                except Exception as err:
                    print(f'{task_name}: synthesis failed!')
                    traceback.print_exc()
                    code = None
                finally:
                    pass
                if code is None:
                    print(f'{task_name}: compile error!')
                    compile_info.compile_errors[data.prog_name] = data.num_snippets
                    continue

                try:
                    module_path = os.path.splitext(code_path)[0]
                    module = importlib.import_module(module_path.replace('/', '.'))
                    func = module.__getattribute__(data.func_name)
                except:
                    print(f'{task_name}: func {data.func_name} not found, compile error!')
                    traceback.print_exc()
                    compile_info.compile_errors[data.prog_name] = data.num_snippets
                    continue
                @timeout_decorator.timeout(time_limit)
                def timeout_func(inp):
                    out = func(inp)
                    return out
                ok = True
                for inp, ans in data.specs:
                    try: 
                        out = timeout_func(inp)
                    except timeout_decorator.TimeoutError as err:
                        print(f'{task_name}: Time limit exceeded at {data.func_name}(\"{inp}\") = \"{ans}\"!')
                        ok = False
                        compile_info.time_limit_exceededs[data.prog_name] = data.num_snippets
                        break
                    except Exception as err:
                        print(f'{task_name}: Runtime error at {data.func_name}(\"{inp}\") = \"{ans}\"!')
                        ok = False
                        compile_info.runtime_errors[data.prog_name] = data.num_snippets
                        break
                    if out != ans: 
                        print(f'{task_name}: Wrong Answer! {data.func_name}(\"{inp}\") should be \"{ans}\"!')
                        ok = False
                        compile_info.wrong_answers[data.prog_name] = data.num_snippets
                        break
                if ok:
                    print(f'{task_name}: Accepted!')
                    compile_info.accepteds[data.prog_name] = data.num_snippets
            except Exception as err:
                print(err)
    finally:
        with open(compile_info_path, 'w') as f:
            f.write(json.dumps(dataclasses.asdict(compile_info)))

if __name__ == '__main__':

    for num_snippets in range(1, 8):
        sampler = ProgramSampler()
        sampler.sample(
            num_snippets=num_snippets,
            program_dir=f'programs_{num_snippets}/',
            program_prefix=f'string_manipulation_{num_snippets}',
            prompt_dir=f'prompts_{num_snippets}/',
            seed=int(f'{num_snippets}114514')
        )
       
        
        anpl_robot = GPT2Code()
        anpl_compiler = ANPLCompiler(max_try_times=5, max_temperature=0.5)

        test_compiler(
            sampler=sampler,
            compiler=anpl_compiler,
            robot=anpl_robot,
            model_name='gpt-3.5-turbo-0301',
            prompt_dir=f'prompts_{num_snippets}/',
            response_dir=f'anpl_responses_{num_snippets}/',
            result_dir=f'anpl_results_{num_snippets}/',
            compile_info_path=f'anpl_compile_info_{num_snippets}.json',
        )
        

        parsel_robot = GPT2Code(parsel_background, parsel_pre_prompt, parsel_post_prompt)
        parsel_robot.extract_code = parsel_extract_code
        parsel_compiler = ParselCompiler()

        test_compiler(
            sampler=sampler,
            compiler=parsel_compiler,
            robot=parsel_robot,
            model_name='gpt-3.5-turbo-0301',
            prompt_dir=f'prompts_{num_snippets}/',
            response_dir=f'parsel_responses_{num_snippets}/',
            result_dir=f'parsel_results_{num_snippets}/',
            compile_info_path=f'parsel_compile_info_{num_snippets}.json',
        )


