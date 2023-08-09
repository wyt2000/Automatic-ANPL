from ProgramBuilder import ProgramBuilder
from GPT2Code import GPT2Code 
from ANPLCompiler import ANPLCompiler
from ParselPrompts import background as parsel_background
from ParselPrompts import pre_prompt as parsel_pre_prompt
from ParselPrompts import post_prompt as parsel_post_prompt
import os
import pathlib
import importlib
import json
import dataclasses

@dataclasses.dataclass
class CompileInfo:
    compiler_name : str = 'anpl'
    compile_errors : dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    accepteds : dict[str, int] = dataclasses.field(default_factory=dict) 

def test_compiler(builder, compiler, robot, model_name, prompt_dir, response_dir, result_dir, compile_info_path):
    builder.mkdir_override(response_dir)
    builder.mkdir_override(result_dir)
    compile_info = CompileInfo(compiler.name)

    for i, data in enumerate(builder.dataset):
        task_name = f"{compiler.name}_{data.name}"
        print(f'{task_name}: requesting for {model_name}...')
        response = robot.request(model_name,
                                 data.func_name,
                                 data.prompt, 
                                 os.path.join(response_dir, f"{task_name}.res"))
        print(f'{task_name} request for {model_name} done!, the response {compiler.name} code is:\n{response}')
        code_path = os.path.join(result_dir, f"{task_name}.py")
        try:
            code = compiler.compile(data.name, response, code_path)
        except Exception as err:
            print(f'{task_name}: synthesis failed!')
            print(err)
            code = None
        if code is None:
            print(f'{task_name}: compile error!')
            compile_info.compile_errors[data.name] = data.block_num
            continue
        module_path = os.path.splitext(code_path)[0]
        module = importlib.import_module(module_path.replace('/', '.'))
        try:
            func = module.__getattribute__(data.func_name)
        except:
            print(f'{task_name}: func {data.func_name} not found, compile error!')
            compile_info.compile_errors[data.name] = data.block_num
            continue
        ok = True
        for inp, out in data.specs:
            if func(inp) != out: 
                print(f'{task_name}: Wrong Answer! {data.func_name}(\"{inp}\") should be \"{out}\"!')
                ok = False
                compile_info.wrong_answers[data.name] = data.block_num
                break
        if ok:
            print(f'{task_name}: Accepted!')
            compile_info.accepteds[data.name] = data.block_num

    with open(compile_info_path, 'w') as f:
        f.write(json.dumps(dataclasses.asdict(compile_info)))

if __name__ == '__main__':
    builder = ProgramBuilder()
    builder.build()
    
    anpl_robot = GPT2Code()
    anpl_compiler = ANPLCompiler(max_try_times=10, max_temperature=1.0)

    test_compiler(
        builder=builder,
        compiler=anpl_compiler,
        robot=anpl_robot,
        model_name='gpt-3.5-turbo-0301',
        prompt_dir='prompts/',
        response_dir='anpl_responses/',
        result_dir='anpl_results/',
        compile_info_path='anpl_compile_info.txt',
    )


