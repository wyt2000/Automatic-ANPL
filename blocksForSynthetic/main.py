from ProgramBuilder import ProgramBuilder
from GPT2ANPL import GPT2ANPL 
from ANPLCompiler import ANPLCompiler
import os
import pathlib
import importlib
import json
import dataclasses

model_name              = 'gpt-3.5-turbo-0301'
prompt_dir              = 'prompts/'
response_dir            = 'responses/'
anpl_result_dir         = 'anpl_results/'
anpl_compile_info_path  = 'anpl_compile_info.txt'

@dataclasses.dataclass
class CompileInfo:
    compiler_name : str = 'anpl'
    compile_errors : dict[str, int] = dataclasses.field(default_factory=dict) 
    wrong_answers : dict[str, int] = dataclasses.field(default_factory=dict) 
    accepteds : dict[str, int] = dataclasses.field(default_factory=dict) 

if __name__ == '__main__':
    builder = ProgramBuilder()
    builder.build()

    robot = GPT2ANPL()
    anpl = ANPLCompiler(max_try_times=20)
    builder.mkdir_override(response_dir)
    builder.mkdir_override(anpl_result_dir)
    anpl_compile_info = CompileInfo('anpl')
    for i, data in enumerate(builder.dataset):
        print(f'{data.name}: Requesting for {model_name}...')
        response = robot.request(model_name, data.func_name, data.prompt, os.path.join(response_dir, data.name+'.res'))
        builder.dataset[i].response = response
        print(f'{data.name}: Request for {model_name} done!, the response anpl program is:\n{response}')
        anpl_code_path = os.path.join(anpl_result_dir, data.name+'.py')
        try:
            anpl_code = anpl.compile(data.name, response, anpl_code_path)
        except:
            print(f'{data.name}: ANPL compile error!')
            anpl_code = None
        builder.dataset[i].anpl = anpl_code 
        if anpl_code is None:
            anpl_compile_info.compile_errors[data.name] = data.block_num
            continue
        module_path = os.path.splitext(anpl_code_path)[0]
        module = importlib.import_module(module_path.replace('/', '.'))
        try:
            func = module.__getattribute__(data.func_name)
        except:
            print(f'{data.name}: ANPL func {data.func_name} not found, compile error!')
            anpl_compile_info.compile_errors[data.name] = data.block_num
            continue
        ok = True
        for inp, out in data.specs:
            if func(inp) != out: 
                print(f'{data.name}: Wrong Answer! {data.func_name}(\"{inp}\") should be \"{out}\"!')
                ok = False
                anpl_compile_info.wrong_answers[data.name] = data.block_num
                break
        if ok:
            print(f'{data.name}: Accepted!')
            anpl_compile_info.accepteds[data.name] = data.block_num

    with open(anpl_compile_info_path, 'w') as f:
        f.write(json.dumps(dataclasses.asdict(anpl_compile_info)))
