from ProgramBuilder import ProgramBuilder
from gpt4toANPL import GPT4toANPL
from ANPLCompiler import ANPLCompiler
import os
import pathlib
import importlib
import json

prompt_dir = 'prompts/'
response_dir = 'responses/'
anpl_result_dir = 'anpl_results/'
anpl_compile_info_path = 'anpl_compile_info.txt'

class CompileInfo:
    def __init__(self, compiler_name='anpl'):
        self.compiler_name = compiler_name
        self.compile_errors = {} 
        self.wrong_answers = {} 
        self.accepteds = {} 

    def asdict(self):
        return {
            "compiler_name"  : self.compiler_name,
            "compile_errors" : self.compile_errors,
            "wrong_answers"  : self.wrong_answers,
            "accepteds"      : self.accepteds
        }

if __name__ == '__main__':
    builder = ProgramBuilder()
    builder.build()

    robot = GPT4toANPL()
    anpl = ANPLCompiler()
    builder.mkdir_override(response_dir)
    builder.mkdir_override(anpl_result_dir)
    anpl_compile_info = CompileInfo('anpl')
    for i, data in enumerate(builder.dataset):
        print(f'{data.name}: Requesting for GPT4...')
        response = robot.request(data.prompt, os.path.join(response_dir, data.name+'.res'))
        builder.dataset[i].response = response
        print(f'{data.name}: Request for GPT4 done!, the response anpl program is:\n{response}')
        anpl_code_path = os.path.join(anpl_result_dir, data.name+'.py')
        anpl_code = anpl.compile(data.name, response, anpl_code_path)
        builder.dataset[i].anpl = anpl_code 
        if anpl_code is None:
            anpl_compile_info.compile_errors[data.name] = data.block_num
            continue
        module_path = os.path.splitext(anpl_code_path)
        module = importlib.import_module(module_path.replace('/', '.'))
        func = module.__getattribute__(data.func_name)
        ok = True
        for inp, out in data.specs:
            if func(inp) != out: 
                print(f'{data.name}: Wrong Answer! {func_name}(\"{inp}\") should be \"{out}\"!')
                ok = False
                anpl_compile_info.wrong_answers[data.name] = data.block_num
                break
        if ok:
            print(f'{data.name}: Accepted!')
            anpl_compile_info.accepteds[data.name] = data.block_num

    with open(anpl_compile_info_path, 'w') as f:
        f.write(json.dumps(anpl_compile_info.asdict()))
