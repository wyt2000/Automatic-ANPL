import os
import traceback
from .ANPL.anpl.parser import ANPLParser
from .Synthesizer import AbstractSynthesizer
from .ANPL.ANPLCompiler import ANPLCompiler
from .ANPL.anpl.synthesizer import Cache

_question_prefix = "----- Background -----\n"

_question_suffix = "\n----- Task -----\n"

def verify_code(anpl_code):
    anpl_parser = ANPLParser()
    anpl = anpl_parser.try_parse(anpl_code, from_user=False)
    if not anpl:
        raise Exception("Compile Error!")
    implemented_funs = {f.name for f in anpl.funs.values() if f.code}
    if 'main' not in implemented_funs:
        raise Exception("There should be one implemented main function!")

class ANPLSynthesizer(AbstractSynthesizer):

    def synthesize(self,
                   task_name: str,
                   anpl_code: str,
                   save_path_prefix: str,
                   cache_path_prefix: str,
                   question: str,
                   inputs: list[str],
                   outputs: list[str],
                   num_completions_list: list[int] = [1]):

        prefix = _question_prefix + question + _question_suffix
        cache = Cache(file_path=f'{cache_path_prefix}.json')
        compiler = ANPLCompiler()
        results = {}
        for num_completions in num_completions_list:
            target_code = None
            try:
                target_code = compiler.compile(
                    task_name       = task_name,
                    entry           = 'main',
                    code            = anpl_code,
                    cache           = cache,
                    input_outputs   = (inputs, outputs),
                    num_completions = num_completions,
                    prefix          = prefix
                )
                results[num_completions] = target_code
            except Exception as err:
                pass
            finally:
                cache.dump()
            if not target_code: 
                continue
            with open(f'{save_path_prefix}_{num_completions}.py', 'w') as f:
                f.write(target_code)
        if not results:
            raise Exception(f"{task_name}: ANPL Synthesis Failed!")
        return results

