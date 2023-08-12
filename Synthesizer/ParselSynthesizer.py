import os
import traceback
from .parsel import parsel
from .Synthesizer import AbstractSynthesizer

class ParselSynthesizer(AbstractSynthesizer):

    cache_path = 'cache.json'
    key_path = 'key.txt'

    @property
    def name(self):
        return 'parsel'

    def synthesize(self, program, save_path, *args):
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

