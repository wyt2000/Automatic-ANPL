from ProgramBuilder import ProgramBuilder
from gpt4toANPL import GPT4toANPL
from ANPLCompiler import ANPLCompiler
import os
import pathlib

prompt_dir = 'prompts/'
response_dir = 'responses/'
if __name__ == '__main__':
    builder = ProgramBuilder()
    builder.build()

    robot = GPT4toANPL()
    builder.mkdir_override(response_dir)
    prompt_paths = list(pathlib.Path(prompt_dir).glob('*.prompt'))
    for path in prompt_paths:
        with open(path, 'r') as f:
            name = pathlib.Path(path).stem
            prompt = f.read()
        print(f'GPT4: Requesting for {name}...')
        robot.request(prompt, os.path.join(response_dir, name+'.res'))
        print(f'GPT4: Request for {name} done!')
 
