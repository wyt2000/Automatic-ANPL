import sys
sys.path.append('./parsel')

from parsel import parsel
import os
import traceback

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

class ParselCompiler:
    name = 'parsel'
    cache_path = 'cache.json'
    key_path = 'key.txt'

    def compile(self, name, program, save_path):
        codegen = parsel.CodeGen(self.cache_path, self.key_path)
        code = None
        try:
            code = parsel.parsel_str(codegen, program, target_file=save_path)
        except Exception as err:
            traceback.print_exc()
            print(err)
        finally:
            if os.path.isfile(self.cache_path):
                os.remove(self.cache_path)
        return code

if __name__ == '__main__':
    compiler = ParselCompiler()
    with open('test.ss', 'r') as f:
        res = compiler.compile('test', f.read(), 'test.py')
    print(res)
