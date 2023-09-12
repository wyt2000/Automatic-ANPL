import os
import traceback
from .parsel import parsel, codex, graph
from .Synthesizer import AbstractSynthesizer

exec_imports = (
    "import sys\nimport time\nimport itertools\nfrom itertools import accumulate, product, permutations, "
    "combinations\nimport collections\nfrom collections import Counter, OrderedDict, deque, defaultdict, "
    "ChainMap\nimport functools\nfrom functools import lru_cache\nimport math\nfrom math import sqrt, sin, cos, tan, ceil, "
    "fabs, floor, gcd, exp, log, log2\nimport fractions\nfrom typing import List, Tuple\nimport numpy as "
    "np\nimport random\nimport heapq\n"
)

_io_template = '''
from sys import stdin

inp = ""
for line in stdin:
    inp += line
print({root}(inp))
'''

class ParselSynthesizer(AbstractSynthesizer):

    # TODO: handle starter code.
    def transform(self, target_code, root):
        return exec_imports + target_code + _io_template.format(root=root)

    def synthesize(self,
                   parsel_code: str,
                   save_path_prefix: str,
                   cache_path_prefix: str,
                   inputs: list[str],
                   outputs: list[str],
                   num_completions_list: list[int] = [1]):

        parsel_code = parsel_code.strip().splitlines()
        root, defined_fns = parsel.get_graph(parsel_code)
        root_name = graph.get_root(defined_fns)
        asserts = []
        for inp, out in zip(inputs, outputs):
            try:
                asserts += [f"{repr(inp.rstrip())} -> {repr(out.rstrip())}"]
            except:
                asserts += [f"{repr(inp)} -> {repr(out)}"]
        root.asserts = asserts
        results = {}
        for num_completions in num_completions_list:
            codeGen = codex.CodeGen(
                cache = f'{cache_path_prefix}.json'
            )
            compiled_fns = parsel.parsel_graph(defined_fns, codeGen, num_completions=num_completions)
            target_code = parsel.fns_to_str(defined_fns[root_name], set())
            target_code = self.transform(target_code, root_name)
            results[num_completions] = target_code
            with open(f'{save_path_prefix}_{num_completions}.py', 'w') as f:
                f.write(target_code)
        return results

if __name__ == '__main__':
    parselSynthesizer = ParselSynthesizer()
    with open('test.ss', 'r') as f:
        parsel_code = f.read()
    parselSynthesizer.synthesize(parsel_code, 'test/test', 'test/test', [1, 2, 4, 8, 16])

