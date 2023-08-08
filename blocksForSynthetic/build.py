import os
import pathlib 
import shutil
import random
import string

class FunctionBuilder():
    alphabet = list(string.ascii_letters) + [' ', '?', '!', '.']

    def __init__(self, input_path='input.txt'):
        self.input_path = input_path
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
        self.block_total = len(codes)

    def build_single_function(self, block_ids, func_name, func_args, func_desc, func_return):
        func = ''
        func += f'def {func_name}({func_args}):\n'
        func += f'    \"\"\"\n    {func_desc}\n'
        op_desc = ''
        op_code = ''
        for idx in block_ids:
            op_desc += f'    - {self.descs[idx]}\n'
            op_code += f'    {self.codes[idx]}\n'
        func += op_desc
        func += '    \"\"\"\n'
        func += op_code
        func += f'    {func_return}\n'
        return func

    def build_specifications(self, func, func_name, spec_num, spec_size):
        exec(func)
        spec = ''
        spec += 'if __name__ == \"__main__\":\n'
        for i in range(spec_num):
            cur_spec_size = random.randint(1, spec_size)
            inp = ''.join(random.choices(self.alphabet, k=cur_spec_size))
            out = eval(f'{func_name}(\"{inp}\")') 
            spec += f'    assert({func_name}(\"{inp}\") == \"{out}\")\n'
        return spec

    def build(self, 
              block_num=7,
              data_size=20,
              func_name="string_manipulation",
              func_args="s: str",
              func_desc="This function takes a string as input, then returns the result of performing the following sequence of manipulations on that string:",
              func_return="return s",
              spec_num=5,
              spec_size=30,
              output_dir='output/',
              output_prefix='string_manipulation'):

        assert(0 <= block_num <= self.block_total) 
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        pathlib.Path(output_dir).mkdir(parents=True)

        for i in range(1, data_size + 1):
            cur_block_num = random.randint(1, block_num)
            block_ids = random.sample(range(self.block_total), cur_block_num)
            func = self.build_single_function(block_ids, func_name, func_args, func_desc, func_return)
            spec = self.build_specifications(func, func_name, spec_num, spec_size)
            result = '\n'.join([func, spec])
            with open(os.path.join(output_dir, output_prefix+f'_{i}.py'), 'w') as f:
                f.write(result)

if __name__ == '__main__':
    builder = FunctionBuilder()
    builder.build()

