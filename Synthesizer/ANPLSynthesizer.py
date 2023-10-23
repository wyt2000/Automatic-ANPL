import os
import traceback
import timeout_decorator
from typing import Iterator 
import ast

from .ANPL.anpl.parser import ANPLParser
from .Synthesizer import AbstractSynthesizer
from .ANPL.ANPLCompiler import ANPLCompiler
from .ANPL.anpl.synthesizer import Cache

_question_prefix = "----- Background -----\n"

_question_suffix = "\n----- Task -----\n"

# Check anpl code is valid in syntax
def verify_code(anpl_code, entry='main'):
    anpl_parser = ANPLParser()
    anpl = anpl_parser.try_parse(anpl_code, from_user=False)
    if not anpl:
        raise Exception("Compile Error!")
    implemented_funs = {f.name for f in anpl.funs.values() if f.code}
    if entry not in implemented_funs:
        raise Exception(f"There should be one implemented function {entry}!")

# TODO: Move it to utils
# Test python code by ANPL synthesizer
def eval_python(task_name: str,
                code: str,
                asserts: list[str]):
    assert_str = '\n'.join(asserts)
    ast.parse(assert_str)
    code, passed_asserts = ANPLCompiler.eval_implementation(code, assert_str, ['', []])
    return passed_asserts 

# Convert io list to assert str
def get_assert_str(asserts: list[str]):
    return '\n'.join(asserts)

# Eval codes from generator with the limit of time.
def eval_sampled_codes(task_name: str,
                       code_generator: Iterator[str],
                       assert_str: str,
                       n_to_try: int,
                       max_time: float):
    compiler = ANPLCompiler()
    return compiler.eval_sampled_codes(task_name, code_generator, assert_str, n_to_try, max_time=max_time)


# Add import and stdin for code
def wrap_code(code: str):
    return ANPLCompiler.transform('main', code)

class ANPLSynthesizer(AbstractSynthesizer):

    def synthesize(self,
                   task_name: str,
                   anpl_code: str,
                   save_path_prefix: str,
                   cache_path_prefix: str,
                   question: str,
                   asserts: list[str],
                   entry: str = 'main',
                   num_completions_list: list[int] = [1]):
        # prefix = _question_prefix + question + _question_suffix
        cache = Cache(file_path=f'{cache_path_prefix}.json')
        compiler = ANPLCompiler()
        results = {}
        for num_completions in num_completions_list:
            target_code = None
            success = False
            try:
                target_code, success = compiler.compile(
                    task_name       = task_name,
                    entry           = entry,
                    code            = anpl_code,
                    cache           = cache,
                    asserts         = asserts,
                    num_completions = num_completions
                )
                results[num_completions] = [target_code, success]
            except Exception as err:
                traceback.print_exc()
                success = False
            finally:
                cache.dump()
        if not results:
            raise Exception(f"{task_name}: ANPL Synthesis Failed!")
        return results

