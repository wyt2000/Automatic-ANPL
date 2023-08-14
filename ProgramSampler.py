import os
import pathlib 
import shutil
import random
import string
import argparse
import dataclasses
import logging

from utils import mkdir_override

@dataclasses.dataclass
class ProgramData():
    '''
    Data of each program sample.
    '''
    prog_name: str
    func_name: str
    num_snippets: int
    prompt: str
    specs: list[tuple[str, str]]

class ProgramSampler():
    '''
    ProgramSampler:
        1. Read input program snippets and descriptions.
        2. Generate prompts and I/O specifications as `ProgramData`.
        3. (Optional) Save correct programs as files.
    '''
    # TODO: Support other input formats, support non-str specs.
    def __init__(self, input_path='input.txt', alphabet=list(string.ascii_letters) + [' ','?','!','.']):
        '''
        :param input_path: Program snippet should be a single line code after a single line description.
                           Two snippets should be seperated by an empty line.
                           See `input.txt` as a reference.
        :type input_path: str
        :param alphabet: Elements used to generate I/O specs.
        :type alphabet: list(str)
        '''
        self.input_path = input_path
        self.alphabet = alphabet
        descs = []
        codes = []
        with open(input_path, 'r') as f:
            while True:
                descs.append(f.readline()[:-1])
                codes.append(f.readline()[:-1])
                if not f.readline():
                    break
        self.descs = descs
        self.codes = codes
        self.total_snippets = len(codes)
        self.dataset = []
        self.logger = logging.getLogger(__name__)

    def _build_op_desc(self, snippet_ids):
        op_desc = []
        for idx in snippet_ids:
            op_desc.append(f'    - {self.descs[idx]}')
        return op_desc

    def _build_prompt(self, func_desc, op_desc):
        return '\n'.join([func_desc, *op_desc]) 

    def _build_func_code(self, snippet_ids, func_name, func_args, func_desc, op_desc, func_return):
        func = ''
        func += f'def {func_name}({func_args}):\n'
        func += f'    \"\"\"\n    {func_desc}\n'
        func += '\n'.join(op_desc)
        func += '    \"\"\"\n'
        for idx in snippet_ids:
            func += f'    {self.codes[idx]}\n'
        func += f'    {func_return}\n'
        return func

    def _build_spec(self, func, func_name, spec_num, max_spec_size):
        specs = []
        exec(func)
        for i in range(spec_num):
            spec_size = random.randint(1, max_spec_size)
            inp = ''.join(random.choices(self.alphabet, k=spec_size))
            out = eval(f'{func_name}(\"{inp}\")') 
            specs.append((inp, out))
        return specs

    def _build_spec_code(self, func_name, specs):
        code = ''
        code += 'if __name__ == \"__main__\":\n'
        for spec in specs:
            inp, out = spec
            code += f'    assert({func_name}(\"{inp}\") == \"{out}\")\n'
        return code 

    def sample(self, 
              num_snippets=7,
              data_size=20,
              func_name='string_manipulation',
              func_args='s: str',
              func_desc='This function takes a string as input, then returns the result of performing the following sequence of manipulations on that string:',
              func_return="return s",
              spec_num=5,
              max_spec_size=30,
              save_correct_program=True,
              program_dir='programs/',
              program_prefix='string_manipulation',
              prompt_dir='prompts/',
              seed=114514):
        '''
        :param num_snippets: Program snippet number in each program case.
        :type num_snippets: int

        :param data_size: Program case number.
        :type data_size: int

        :param func_name: Function name, which will be used in prompt wrapper.
        :type func_name: str

        :param func_args: Only support str now.
        :type func_args: str

        :param func_return: Only support `return s` now.
        :type func_return: str

        :param spec_num: I/O specification number in one program.
        :type spec_num: int 

        :param max_spec_size: Max input length in I/O specification.
        :type max_spec_size: int

        :param save_correct_program: True if save correct program in `program_dir`
        :type save_correct_program: str
        
        :param program_dir
        :type program_dir: str

        :param program_prefix: `prog_name` will be {program_prefix}_{idx}
        :type program_prefix: str

        :param prompt_dir
        :type prompt_dir: str

        :param seed: random seed for `random.sample`
        :type seed: int

        :return: dataset.
        :rtype: list

        '''
        assert(0 <= num_snippets <= self.total_snippets) 
        self.logger.info(f'Generating {data_size} programs, each has {num_snippets} snippets...')
        random.seed(seed)
        mkdir_override(prompt_dir)
        if save_correct_program:
            mkdir_override(program_dir)
        try:
            for i in range(1, data_size + 1):
                snippet_ids = random.sample(range(self.total_snippets), num_snippets)
                op_desc     = self._build_op_desc(snippet_ids)
                prompt      = self._build_prompt(func_desc, op_desc)
                func_code   = self._build_func_code(snippet_ids, func_name, func_args, func_desc, op_desc, func_return)
                specs       = self._build_spec(func_code, func_name, spec_num, max_spec_size)
                spec_code   = self._build_spec_code(func_name, specs)
                prog_name   = program_prefix+f'_{i}'
                self.dataset.append(ProgramData(prog_name, func_name, num_snippets, prompt, specs))
                with open(os.path.join(prompt_dir, prog_name+'.prompt'), 'w') as f:
                    f.write(prompt)

                if save_correct_program:
                    prog      = '\n'.join([func_code, spec_code])
                    with open(os.path.join(program_dir, prog_name+'.py'), 'w') as f:
                        f.write(prog)
        except Exception:
            self.logger.exception(f'Error occurs during program samping!')
            exit(1)

        self.logger.info(f'Program sampling done!')
        return self.dataset

if __name__ == '__main__':
    sampler = ProgramSampler()
    sampler.sample()

